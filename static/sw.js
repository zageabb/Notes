/* Network-only for all data and navigation: never cache private Notes content. */
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => { /* Leave all requests to browser/network. */ });
