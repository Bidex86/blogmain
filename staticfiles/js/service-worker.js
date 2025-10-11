// static/js/service-worker.js
const CACHE_NAME = 'blog-pwa-v1.0.0';
const STATIC_CACHE_URLS = [
    '/',
    // Reference Pipeline compiled assets
    '{% load pipeline %}{% stylesheet_url "main" %}', // This will resolve to /static/css/main.min.css (or versioned filename)
    '{% load pipeline %}{% javascript_url "main" %}', // This will resolve to /static/js/main.min.js (or versioned filename)
    '/static/images/logo.png',
    '/static/images/placeholder.jpg',
    '/offline/',
    '/manifest.json'
];

const DYNAMIC_CACHE_NAME = 'blog-dynamic-v1.0.0';
const MAX_DYNAMIC_CACHE_SIZE = 50;

// Install event - cache static assets
self.addEventListener('install', event => {
    console.log('Service Worker installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Caching static assets');
                return cache.addAll(STATIC_CACHE_URLS);
            })
            .then(() => {
                return self.skipWaiting();
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker activating...');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME && cacheName !== DYNAMIC_CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            return self.clients.claim();
        })
    );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', event => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') {
        return;
    }

    // Skip external requests
    if (!event.request.url.startsWith(self.location.origin)) {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then(cachedResponse => {
                if (cachedResponse) {
                    // Return cached version
                    return cachedResponse;
                }

                // Fetch from network
                return fetch(event.request)
                    .then(response => {
                        // Don't cache non-successful responses
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Cache dynamic content
                        if (shouldCacheDynamically(event.request)) {
                            const responseToCache = response.clone();
                            caches.open(DYNAMIC_CACHE_NAME)
                                .then(cache => {
                                    cache.put(event.request, responseToCache);
                                    limitCacheSize(DYNAMIC_CACHE_NAME, MAX_DYNAMIC_CACHE_SIZE);
                                });
                        }

                        return response;
                    })
                    .catch(() => {
                        // Offline fallback
                        if (event.request.destination === 'document') {
                            return caches.match('/offline/');
                        }
                        
                        if (event.request.destination === 'image') {
                            return caches.match('/static/images/placeholder.jpg');
                        }
                    });
            })
    );
});

// Background sync for form submissions
self.addEventListener('sync', event => {
    console.log('Background sync triggered:', event.tag);
    
    if (event.tag === 'comment-sync') {
        event.waitUntil(syncComments());
    }
    
    if (event.tag === 'newsletter-sync') {
        event.waitUntil(syncNewsletterSignup());
    }
});

// Push notification handler
self.addEventListener('push', event => {
    console.log('Push notification received');
    
    let data = {};
    if (event.data) {
        data = event.data.json();
    }

    const options = {
        body: data.body || 'New blog post available!',
        icon: '/static/images/icon-192x192.png',
        badge: '/static/images/badge-72x72.png',
        image: data.image || '/static/images/notification-banner.jpg',
        tag: data.tag || 'blog-notification',
        data: {
            url: data.url || '/',
            timestamp: Date.now()
        },
        actions: [
            {
                action: 'read',
                title: 'Read Now',
                icon: '/static/images/read-icon.png'
            },
            {
                action: 'dismiss',
                title: 'Dismiss',
                icon: '/static/images/dismiss-icon.png'
            }
        ],
        requireInteraction: true,
        vibrate: [200, 100, 200]
    };

    event.waitUntil(
        self.registration.showNotification(
            data.title || 'New Blog Post',
            options
        )
    );
});

// Notification click handler
self.addEventListener('notificationclick', event => {
    console.log('Notification clicked:', event.notification.tag);
    event.notification.close();

    if (event.action === 'read') {
        const url = event.notification.data.url || '/';
        event.waitUntil(
            clients.matchAll({ type: 'window' }).then(clientList => {
                // Check if there's already a window open
                for (let client of clientList) {
                    if (client.url === url && 'focus' in client) {
                        return client.focus();
                    }
                }
                
                // Open new window
                if (clients.openWindow) {
                    return clients.openWindow(url);
                }
            })
        );
    } else if (event.action === 'dismiss') {
        // Just close the notification
        console.log('Notification dismissed');
    }
});

// Helper functions
function shouldCacheDynamically(request) {
    const url = request.url;
    
    // Cache blog posts
    if (url.includes('/blog/') || url.includes('/category/')) {
        return true;
    }
    
    // Cache API responses
    if (url.includes('/api/')) {
        return true;
    }
    
    // Cache images
    if (request.destination === 'image') {
        return true;
    }
    
    return false;
}

function limitCacheSize(cacheName, maxSize) {
    caches.open(cacheName)
        .then(cache => {
            cache.keys().then(keys => {
                if (keys.length > maxSize) {
                    // Delete oldest entries
                    const deletePromises = keys.slice(0, keys.length - maxSize)
                        .map(key => cache.delete(key));
                    return Promise.all(deletePromises);
                }
            });
        });
}

async function syncComments() {
    try {
        // Get pending comments from IndexedDB
        const pendingComments = await getPendingComments();
        
        for (const comment of pendingComments) {
            try {
                const response = await fetch('/comments/add/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': comment.csrfToken
                    },
                    body: JSON.stringify(comment.data)
                });
                
                if (response.ok) {
                    // Remove from pending queue
                    await removePendingComment(comment.id);
                    console.log('Comment synced successfully');
                }
            } catch (error) {
                console.error('Failed to sync comment:', error);
            }
        }
    } catch (error) {
        console.error('Comment sync failed:', error);
    }
}

async function syncNewsletterSignup() {
    try {
        const pendingSignups = await getPendingNewsletterSignups();
        
        for (const signup of pendingSignups) {
            try {
                const response = await fetch('/newsletter/subscribe/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': signup.csrfToken
                    },
                    body: JSON.stringify(signup.data)
                });
                
                if (response.ok) {
                    await removePendingNewsletterSignup(signup.id);
                    console.log('Newsletter signup synced successfully');
                }
            } catch (error) {
                console.error('Failed to sync newsletter signup:', error);
            }
        }
    } catch (error) {
        console.error('Newsletter sync failed:', error);
    }
}

// IndexedDB helpers (simplified - you'd want to use a library like Dexie.js)
function getPendingComments() {
    return new Promise((resolve) => {
        // Implementation would get pending comments from IndexedDB
        resolve([]);
    });
}

function removePendingComment(id) {
    return new Promise((resolve) => {
        // Implementation would remove comment from IndexedDB
        resolve();
    });
}

function getPendingNewsletterSignups() {
    return new Promise((resolve) => {
        resolve([]);
    });
}

function removePendingNewsletterSignup(id) {
    return new Promise((resolve) => {
        resolve();
    });
}

