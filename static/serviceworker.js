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
function sendTokenToServer(token) {
    fetch("{% url 'board:subscribe' %}", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')  // Fetch CSRF token
        },
        body: new URLSearchParams({
            'token': token
        })
    }).then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                console.log('Token successfully sent to the server');
            } else {
                console.error('Error sending token:', data.message);
            }
        }).catch(error => {
            console.error('Request failed', error);
        });
}
