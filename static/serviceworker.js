const CACHE_NAME = 'board4dng-cache-v1';
const urlsToCache = [
    '/',
    '/static/css/styles.css',
    '/static/js/app.js',
    '/static/images/icons/icon-192x192.png',
    '/static/images/icons/icon-512x512.png'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {

                return cache.addAll(urlsToCache);
            })
    );
});


                self.addEventListener('fetch', event => {
                    event.respondWith(
                        caches.match(event.request)
                            .then(response => {
                                return response || fetch(event.request);
                            })
                    );
                });
// serviceworker.js

// Listen for push events
self.addEventListener('push', function (event) {
    const data = event.data.json();
    const title = data.title || 'New Message';
    const options = {
        body: data.body,
        icon: '/static/images/icons/icon-128x128.png',
        badge: '/static/images/icons/icon-128x128.png',
    };
    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Handle notification click
self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    event.waitUntil(
        clients.openWindow('/')
    );
});
