class AnalyticsManager {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.userId = this.getUserId();
        this.startTime = Date.now();
        this.maxScroll = 0;
        this.events = [];
        
        this.init();
    }

    init() {
        this.trackPageView();
        this.setupScrollTracking();
        this.setupTimeTracking();
        this.setupCoreWebVitals();
        this.setupInteractionTracking();
        this.setupPerformanceTracking();
    }

    trackPageView() {
        this.trackEvent('page_view', {
            url: window.location.href,
            title: document.title,
            referrer: document.referrer
        });
    }

    setupScrollTracking() {
        let ticking = false;
        
        const updateScrollDepth = () => {
            const scrolled = window.pageYOffset;
            const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrollPercent = Math.round((scrolled / totalHeight) * 100);
            
            if (scrollPercent > this.maxScroll) {
                this.maxScroll = scrollPercent;
                
                // Track significant scroll milestones
                if (scrollPercent >= 25 && this.maxScroll < 25) {
                    this.trackEvent('scroll_depth', { depth: 25 });
                } else if (scrollPercent >= 50 && this.maxScroll < 50) {
                    this.trackEvent('scroll_depth', { depth: 50 });
                } else if (scrollPercent >= 75 && this.maxScroll < 75) {
                    this.trackEvent('scroll_depth', { depth: 75 });
                } else if (scrollPercent >= 90 && this.maxScroll < 90) {
                    this.trackEvent('scroll_depth', { depth: 90 });
                }
            }
            
            ticking = false;
        };

        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(updateScrollDepth);
                ticking = true;
            }
        });
    }

    setupTimeTracking() {
        // Track time on page when user leaves
        const trackTimeOnPage = () => {
            const duration = Date.now() - this.startTime;
            this.trackEvent('time_on_page', { duration: Math.round(duration / 1000) });
        };

        window.addEventListener('beforeunload', trackTimeOnPage);
        
        // Also track at intervals for active users
        setInterval(() => {
            if (document.visibilityState === 'visible') {
                const duration = Date.now() - this.startTime;
                this.trackEvent('time_on_page', { duration: Math.round(duration / 1000) });
            }
        }, 30000); // Every 30 seconds
    }

    setupCoreWebVitals() {
        // Largest Contentful Paint
        new PerformanceObserver((entryList) => {
            const entries = entryList.getEntries();
            const lastEntry = entries[entries.length - 1];
            this.trackCoreWebVital('lcp', lastEntry.startTime);
        }).observe({ entryTypes: ['largest-contentful-paint'] });

        // First Input Delay
        new PerformanceObserver((entryList) => {
            const firstInput = entryList.getEntries()[0];
            this.trackCoreWebVital('fid', firstInput.processingStart - firstInput.startTime);
        }).observe({ entryTypes: ['first-input'] });

        // Cumulative Layout Shift
        let clsValue = 0;
        new PerformanceObserver((entryList) => {
            for (const entry of entryList.getEntries()) {
                if (!entry.hadRecentInput) {
                    clsValue += entry.value;
                }
            }
            this.trackCoreWebVital('cls', clsValue);
        }).observe({ entryTypes: ['layout-shift'] });

        // First Contentful Paint
        new PerformanceObserver((entryList) => {
            const entries = entryList.getEntries();
            const fcp = entries.find(entry => entry.name === 'first-contentful-paint');
            if (fcp) {
                this.trackCoreWebVital('fcp', fcp.startTime);
            }
        }).observe({ entryTypes: ['paint'] });
    }

    setupInteractionTracking() {
        // Track link clicks
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (link) {
                this.trackEvent('link_clicked', {
                    url: link.href,
                    text: link.textContent.trim(),
                    internal: link.hostname === window.location.hostname
                });
            }
        });

        // Track form submissions
        document.addEventListener('submit', (e) => {
            const form = e.target;
            this.trackEvent('form_submitted', {
                form_id: form.id,
                form_class: form.className,
                action: form.action
            });
        });

        // Track comment posting
        const commentForms = document.querySelectorAll('.comment-form');
        commentForms.forEach(form => {
            form.addEventListener('submit', () => {
                this.trackEvent('comment_posted', {
                    post_id: form.dataset.postId
                });
            });
        });
    }

    setupPerformanceTracking() {
        window.addEventListener('load', () => {
            setTimeout(() => {
                const navTiming = performance.getEntriesByType('navigation')[0];
                
                this.trackEvent('performance_metrics', {
                    dom_content_loaded: navTiming.domContentLoadedEventEnd - navTiming.navigationStart,
                    load_complete: navTiming.loadEventEnd - navTiming.navigationStart,
                    ttfb: navTiming.responseStart - navTiming.requestStart,
                    dns_lookup: navTiming.domainLookupEnd - navTiming.domainLookupStart,
                    connection_time: navTiming.connectEnd - navTiming.connectStart
                });
            }, 1000);
        });
    }

    trackCoreWebVital(metric, value) {
        fetch('/api/analytics/core-web-vitals/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                url: window.location.href,
                session_id: this.sessionId,
                [metric]: value,
                device_type: this.getDeviceType(),
                connection_type: this.getConnectionType()
            })
        }).catch(() => {}); // Fail silently
    }

    trackEvent(eventType, eventData = {}) {
        const event = {
            event_type: eventType,
            session_id: this.sessionId,
            user_id: this.userId,
            event_data: eventData,
            timestamp: new Date().toISOString(),
            url: window.location.href
        };

        // Store locally and send in batches
        this.events.push(event);
        
        if (this.events.length >= 10 || eventType === 'page_view') {
            this.sendEvents();
        }
    }

    sendEvents() {
        if (this.events.length === 0) return;

        fetch('/api/analytics/events/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({ events: this.events })
        }).then(() => {
            this.events = [];
        }).catch(() => {
            // Keep events for retry
        });
    }

    generateSessionId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    getUserId() {
        let userId = localStorage.getItem('analytics_user_id');
        if (!userId) {
            userId = 'user_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
            localStorage.setItem('analytics_user_id', userId);
        }
        return userId;
    }

    getDeviceType() {
        const userAgent = navigator.userAgent.toLowerCase();
        if (/mobile|android|iphone|ipad|phone/i.test(userAgent)) {
            return 'mobile';
        } else if (/tablet|ipad/i.test(userAgent)) {
            return 'tablet';
        }
        return 'desktop';
    }

    getConnectionType() {
        return navigator.connection ? navigator.connection.effectiveType : 'unknown';
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
}

// Initialize analytics
const analyticsManager = new AnalyticsManager();

// Enhanced Google Analytics 4 setup
if (typeof gtag !== 'undefined') {
    // Enhanced ecommerce tracking for blog engagement
    gtag('config', 'GA_MEASUREMENT_ID', {
        custom_map: {
            'custom_parameter_1': 'scroll_depth',
            'custom_parameter_2': 'time_on_page'
        }
    });

    // Track enhanced blog reading events
    gtag('event', 'page_view', {
        page_title: document.title,
        page_location: window.location.href,
        content_group1: document.querySelector('[data-category]')?.dataset.category || 'uncategorized',
        content_group2: document.querySelector('[data-author]')?.dataset.author || 'unknown'
    });
}