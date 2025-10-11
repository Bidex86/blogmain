// static/js/pwa-manager.js
class PWAManager {
    constructor() {
        this.swRegistration = null;
        this.isOnline = navigator.onLine;
        this.deferredPrompt = null;
        
        this.init();
    }

    async init() {
        // Register service worker
        await this.registerServiceWorker();
        
        // Setup offline/online detection
        this.setupOnlineOfflineHandlers();
        
        // Setup install prompt
        this.setupInstallPrompt();
        
        // Setup push notifications
        this.setupPushNotifications();
        
        // Setup background sync
        this.setupBackgroundSync();
    }

    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                this.swRegistration = await navigator.serviceWorker.register('/sw.js', {
                    scope: '/'
                });
                
                console.log('Service Worker registered:', this.swRegistration);
                
                // Handle updates
                this.swRegistration.addEventListener('updatefound', () => {
                    const newWorker = this.swRegistration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showUpdateAvailable();
                        }
                    });
                });
                
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }

    setupOnlineOfflineHandlers() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.showConnectionStatus('back online', 'success');
            this.syncPendingData();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.showConnectionStatus('offline - some features may be limited', 'warning');
        });
    }

    setupInstallPrompt() {
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallButton();
        });

        // Handle successful installation
        window.addEventListener('appinstalled', () => {
            console.log('PWA was installed');
            this.hideInstallButton();
            this.deferredPrompt = null;
        });
    }

    showInstallButton() {
        const installButton = document.getElementById('pwa-install-btn');
        if (installButton) {
            installButton.style.display = 'block';
            installButton.addEventListener('click', () => this.promptInstall());
        }
    }

    hideInstallButton() {
        const installButton = document.getElementById('pwa-install-btn');
        if (installButton) {
            installButton.style.display = 'none';
        }
    }

    async promptInstall() {
        if (this.deferredPrompt) {
            this.deferredPrompt.prompt();
            const { outcome } = await this.deferredPrompt.userChoice;
            console.log('User choice:', outcome);
            this.deferredPrompt = null;
        }
    }

    async setupPushNotifications() {
    // Disabled - using push-notifications.js instead
        console.log('Push notifications handled by push-notifications.js');
        return;
    }

    async subscribeToPush() {
        try {
            const subscription = await this.swRegistration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
            });

            // Send subscription to server
            await fetch('/api/push/subscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    subscription: subscription.toJSON()
                })
            });

            console.log('Push subscription successful');
        } catch (error) {
            console.error('Push subscription failed:', error);
        }
    }

    setupBackgroundSync() {
        // Handle form submissions for offline sync
        document.addEventListener('submit', (e) => {
            if (!this.isOnline) {
                const form = e.target;
                
                if (form.classList.contains('comment-form')) {
                    e.preventDefault();
                    this.handleOfflineCommentSubmission(form);
                } else if (form.classList.contains('newsletter-form')) {
                    e.preventDefault();
                    this.handleOfflineNewsletterSubmission(form);
                }
            }
        });
    }

    async handleOfflineCommentSubmission(form) {
        const formData = new FormData(form);
        const commentData = {
            content: formData.get('content'),
            post_id: formData.get('post_id'),
            parent_id: formData.get('parent_id') || null
        };

        // Store in IndexedDB for later sync
        await this.storeForBackgroundSync('comment', commentData);
        
        // Register for background sync
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            await this.swRegistration.sync.register('comment-sync');
        }

        this.showMessage('Comment saved! It will be posted when you\'re back online.', 'info');
    }

    async handleOfflineNewsletterSubmission(form) {
        const formData = new FormData(form);
        const signupData = {
            email: formData.get('email'),
            name: formData.get('name') || ''
        };

        await this.storeForBackgroundSync('newsletter', signupData);
        
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            await this.swRegistration.sync.register('newsletter-sync');
        }

        this.showMessage('Subscription saved! You\'ll be subscribed when back online.', 'info');
    }

    async storeForBackgroundSync(type, data) {
        // Simple IndexedDB storage - in production, use a library like Dexie.js
        const db = await this.openDB();
        const transaction = db.transaction(['pending'], 'readwrite');
        const store = transaction.objectStore('pending');
        
        await store.add({
            type: type,
            data: data,
            timestamp: Date.now(),
            csrfToken: this.getCSRFToken()
        });
    }

    openDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('BlogPWADB', 1);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('pending')) {
                    const store = db.createObjectStore('pending', { keyPath: 'id', autoIncrement: true });
                    store.createIndex('type', 'type');
                    store.createIndex('timestamp', 'timestamp');
                }
            };
        });
    }

    showConnectionStatus(message, type) {
        const statusEl = document.getElementById('connection-status') || this.createStatusElement();
        statusEl.textContent = `You are ${message}`;
        statusEl.className = `connection-status ${type}`;
        statusEl.style.display = 'block';
        
        if (type === 'success') {
            setTimeout(() => {
                statusEl.style.display = 'none';
            }, 3000);
        }
    }

    createStatusElement() {
        const statusEl = document.createElement('div');
        statusEl.id = 'connection-status';
        statusEl.className = 'connection-status';
        document.body.appendChild(statusEl);
        return statusEl;
    }

    showMessage(message, type) {
        // Implementation for showing user messages
        const messageEl = document.createElement('div');
        messageEl.className = `message ${type}`;
        messageEl.textContent = message;
        document.body.appendChild(messageEl);
        
        setTimeout(() => {
            messageEl.remove();
        }, 5000);
    }

    showUpdateAvailable() {
        const updateBanner = document.createElement('div');
        updateBanner.className = 'update-banner';
        updateBanner.innerHTML = `
            <p>A new version is available!</p>
            <button onclick="pwaManager.updateApp()">Update</button>
            <button onclick="this.parentElement.remove()">Later</button>
        `;
        document.body.appendChild(updateBanner);
    }

    updateApp() {
        if (this.swRegistration && this.swRegistration.waiting) {
            this.swRegistration.waiting.postMessage({ action: 'skipWaiting' });
            window.location.reload();
        }
    }

    async syncPendingData() {
        // Trigger background sync for pending data
        if (this.swRegistration && 'sync' in window.ServiceWorkerRegistration.prototype) {
            try {
                await this.swRegistration.sync.register('comment-sync');
                await this.swRegistration.sync.register('newsletter-sync');
            } catch (error) {
                console.error('Background sync registration failed:', error);
            }
        }
    }

    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
}

// Initialize PWA Manager
const VAPID_PUBLIC_KEY = 'YOUR_VAPID_PUBLIC_KEY_HERE'; // Replace with actual key
const pwaManager = new PWAManager();