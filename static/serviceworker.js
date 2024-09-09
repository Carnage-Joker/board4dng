<<<<<<< HEAD
const CACHE_NAME = 'message-board-cache-v1';
const urlsToCache = [
    '/',
    '/static/css/styles.css',
    '/static/js/main.js',
];

self.addEventListener('install', function (event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function (cache) {
=======
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
>>>>>>> c28221110546ac4323e7cd76486121e1b7cfb71e
                return cache.addAll(urlsToCache);
            })
    );
});

<<<<<<< HEAD
self.addEventListener('fetch', function (event) {
    event.respondWith(
        caches.match(event.request)
            .then(function (response) {
=======
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
>>>>>>> c28221110546ac4323e7cd76486121e1b7cfb71e
                return response || fetch(event.request);
            })
    );
});
