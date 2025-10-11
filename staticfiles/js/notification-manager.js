// Notification Manager
class NotificationManager {
    constructor() {
        this.bellBtn = document.getElementById('notificationBellBtn');
        this.dropdown = document.getElementById('notificationDropdown');
        this.badge = document.getElementById('notificationBadge');
        this.statusDot = document.getElementById('notificationStatus');
        this.notificationList = document.getElementById('notificationList');
        this.toggleBtn = document.getElementById('toggleNotificationsBtn');
        this.toggleText = document.getElementById('notificationToggleText');
        this.markAllReadBtn = document.getElementById('markAllReadBtn');
        
        this.isSubscribed = false;
        this.notifications = [];
        
        this.init();
    }

    async init() {
        if (!this.bellBtn) return;
        
        // Setup event listeners
        this.bellBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown();
        });
        
        this.toggleBtn?.addEventListener('click', () => this.toggleSubscription());
        this.markAllReadBtn?.addEventListener('click', () => this.markAllAsRead());
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.dropdown?.contains(e.target) && e.target !== this.bellBtn) {
                this.dropdown.style.display = 'none';
            }
        });
        
        // Check subscription status
        await this.checkSubscriptionStatus();
        
        // Load notifications
        await this.loadNotifications();
        
        // Poll for new notifications every 30 seconds
        setInterval(() => this.loadNotifications(), 30000);
    }

    async checkSubscriptionStatus() {
        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            
            this.isSubscribed = subscription !== null;
            this.updateUI();
        } catch (error) {
            console.error('Error checking subscription:', error);
        }
    }

    updateUI() {
        if (this.isSubscribed) {
            this.statusDot?.classList.add('active');
            this.statusDot?.classList.remove('inactive');
            this.toggleBtn?.classList.remove('disabled');
            if (this.toggleText) {
                this.toggleText.textContent = 'Disable Notifications';
            }
        } else {
            this.statusDot?.classList.remove('active');
            this.statusDot?.classList.add('inactive');
            this.toggleBtn?.classList.add('disabled');
            if (this.toggleText) {
                this.toggleText.textContent = 'Enable Notifications';
            }
        }
    }

    toggleDropdown() {
        const isVisible = this.dropdown.style.display === 'block';
        this.dropdown.style.display = isVisible ? 'none' : 'block';
        
        if (!isVisible) {
            this.loadNotifications();
        }
    }

    async toggleSubscription() {
        if (this.isSubscribed) {
            await this.unsubscribe();
        } else {
            await this.subscribe();
        }
    }

    async subscribe() {
        try {
            const registration = await navigator.serviceWorker.ready;
            
            function urlBase64ToUint8Array(base64String) {
                const padding = '='.repeat((4 - base64String.length % 4) % 4);
                const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');
                const rawData = window.atob(base64);
                const outputArray = new Uint8Array(rawData.length);
                for (let i = 0; i < rawData.length; ++i) {
                    outputArray[i] = rawData.charCodeAt(i);
                }
                return outputArray;
            }
            
            const subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array(window.VAPID_PUBLIC_KEY)
            });
            
            const response = await fetch('/notifications/subscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(subscription.toJSON())
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.isSubscribed = true;
                this.updateUI();
                this.showToast('Notifications enabled successfully!', 'success');
            }
        } catch (error) {
            console.error('Subscription failed:', error);
            this.showToast('Failed to enable notifications', 'error');
        }
    }

    async unsubscribe() {
        try {
            const registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            
            if (subscription) {
                await subscription.unsubscribe();
                
                await fetch('/notifications/unsubscribe/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCookie('csrftoken')
                    },
                    body: JSON.stringify(subscription.toJSON())
                });
            }
            
            this.isSubscribed = false;
            this.updateUI();
            this.showToast('Notifications disabled', 'info');
        } catch (error) {
            console.error('Unsubscribe failed:', error);
            this.showToast('Failed to disable notifications', 'error');
        }
    }

    async loadNotifications() {
        try {
            const response = await fetch('/notifications/list/');
            const data = await response.json();
            
            this.notifications = data.notifications || [];
            this.renderNotifications();
            this.updateBadge();
        } catch (error) {
            console.error('Failed to load notifications:', error);
        }
    }

    renderNotifications() {
        if (!this.notificationList) return;
        
        if (this.notifications.length === 0) {
            this.notificationList.innerHTML = `
                <div class="notification-empty">
                    <i class="bi bi-bell-slash" style="font-size: 48px; color: #ddd;"></i>
                    <p>No notifications yet</p>
                </div>
            `;
            return;
        }
        
        this.notificationList.innerHTML = this.notifications.map(notif => `
            <div class="notification-item ${notif.is_read ? '' : 'unread'}" 
                 data-id="${notif.id}"
                 onclick="notificationManager.handleNotificationClick(${notif.id}, '${notif.url}')">
                <div class="notification-icon">
                    <i class="bi ${this.getNotificationIcon(notif.type)}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${this.escapeHtml(notif.title)}</div>
                    <div class="notification-message">${this.escapeHtml(notif.message)}</div>
                    <div class="notification-time">${this.formatTime(notif.created_at)}</div>
                </div>
            </div>
        `).join('');
    }

    getNotificationIcon(type) {
        const icons = {
            'new_post': 'bi-file-earmark-text',
            'new_comment': 'bi-chat-dots',
            'comment_reply': 'bi-reply',
            'system': 'bi-info-circle'
        };
        return icons[type] || 'bi-bell';
    }

    updateBadge() {
        const unreadCount = this.notifications.filter(n => !n.is_read).length;
        
        if (unreadCount > 0) {
            this.badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
            this.badge.style.display = 'block';
        } else {
            this.badge.style.display = 'none';
        }
    }

    async handleNotificationClick(notifId, url) {
        // Mark as read
        await fetch(`/notifications/${notifId}/mark-read/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken')
            }
        });
        
        // Reload notifications
        await this.loadNotifications();
        
        // Navigate to URL
        if (url) {
            window.location.href = url;
        }
    }

    async markAllAsRead() {
        try {
            await fetch('/notifications/mark-all-read/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken')
                }
            });
            
            await this.loadNotifications();
            this.showToast('All notifications marked as read', 'success');
        } catch (error) {
            console.error('Failed to mark all as read:', error);
        }
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000); // seconds
        
        if (diff < 60) return 'Just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
        
        return date.toLocaleDateString();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
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

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
            color: white;
            border-radius: 4px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.body.dataset.userAuthenticated === 'true') {
        window.notificationManager = new NotificationManager();
    }
});