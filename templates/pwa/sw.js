// Service Worker for Push Notifications
const CACHE_NAME = 'blog-pwa-v1.0.0';

// Install event - don't cache anything on install
self.addEventListener('install', event => {
    console.log('Service Worker installing...');
    event.waitUntil(
        Promise.resolve().then(() => {
            console.log('Install complete');
            return self.skipWaiting();
        })
    );
});

// Activate event
self.addEventListener('activate', event => {
    console.log('Service Worker activating...');
    event.waitUntil(
        Promise.resolve().then(() => {
            console.log('Activate complete');
            return self.clients.claim();
        })
    );
});

// Fetch event - just pass through
self.addEventListener('fetch', event => {
    event.respondWith(fetch(event.request));
});

// Push notification handler
self.addEventListener('push', event => {
    console.log('Push notification received:', event);
    
    let data = { title: 'New Notification', body: 'You have a new update!' };
    
    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            data.body = event.data.text();
        }
    }

    const options = {
        body: data.body || 'New blog post available!',
        icon: '/static/images/icon-192x192.png',
        badge: '/static/images/icon-192x192.png',
        data: { url: data.url || '/' }
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
    console.log('Notification clicked');
    event.notification.close();
    
    event.waitUntil(
        clients.openWindow(event.notification.data.url || '/')
    );
});