// Push Notification Manager
class PushNotificationManager {
    constructor() {
        this.publicKey = window.VAPID_PUBLIC_KEY; // Read from global variable
        this.isSupported = 'serviceWorker' in navigator && 'PushManager' in window;
    }
    // ... rest of the code


    async initialize() {
        if (!this.isSupported) {
            console.log('Push notifications not supported');
            return false;
        }

        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
            await this.subscribeUser();
            return true;
        }
        return false;
    }

    async subscribeUser() {
        try {
            const registration = await navigator.serviceWorker.ready;
            
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(this.publicKey)
            });

            // Send subscription to server
            await fetch('/notifications/subscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(subscription.toJSON())
            });

            console.log('Push subscription successful');
        } catch (error) {
            console.error('Failed to subscribe:', error);
        }
    }

    async unsubscribeUser() {
        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            
            if (subscription) {
                await subscription.unsubscribe();
                
                // Notify server
                await fetch('/notifications/unsubscribe/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCookie('csrftoken')
                    },
                    body: JSON.stringify(subscription.toJSON())
                });
            }
        } catch (error) {
            console.error('Failed to unsubscribe:', error);
        }
    }

    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const pushManager = new PushNotificationManager();
    
    // Auto-initialize for logged-in users
    if (document.body.dataset.userAuthenticated === 'true') {
        // Show notification prompt after 5 seconds
        setTimeout(() => {
            pushManager.initialize();
        }, 5000);
    }
});
