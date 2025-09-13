// service-worker.js
// Place this file in your Django static root directory

const CACHE_NAME = 'blog-cache-v1';
const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  // Add other static assets you want to cache
];

// Install event
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        return self.skipWaiting();
      })
  );
});

// Fetch event
self.addEventListener('fetch', event => {
  // Only handle GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  // Skip cross-origin requests
  if (!event.request.url.startsWith(self.location.origin)) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version if available
        if (response) {
          return response;
        }

        // Clone the request because it's a stream
        const fetchRequest = event.request.clone();

        return fetch(fetchRequest).then(response => {
          // Check if valid response
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }

          // Clone the response because it's a stream
          const responseToCache = response.clone();

          caches.open(CACHE_NAME)
            .then(cache => {
              // Only cache certain types of content
              if (shouldCache(event.request.url)) {
                cache.put(event.request, responseToCache);
              }
            });

          return response;
        }).catch(() => {
          // Return offline page or cached content if available
          return caches.match('/offline.html') || 
                 caches.match(event.request);
        });
      })
  );
});

// Activate event
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// Helper function to determine what to cache
function shouldCache(url) {
  // Cache static assets and images
  return url.includes('/static/') || 
         url.includes('/media/') ||
         url.match(/\.(css|js|png|jpg|jpeg|gif|svg|webp)$/i);
}