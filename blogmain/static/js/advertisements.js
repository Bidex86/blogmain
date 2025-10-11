// static/js/advertisements.js

class AdManager {
    constructor() {
        this.viewedAds = new Set();
        this.clickedAds = new Set();
        this.observers = new Map();
        this.init();
    }

    init() {
        this.setupIntersectionObservers();
        this.setupClickTracking();
        this.detectAdBlocker();
        this.loadPopupAds();
    }

    setupIntersectionObservers() {
        const adContainers = document.querySelectorAll('.advertisement-container');
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const adId = entry.target.dataset.adId;
                    if (adId && !this.viewedAds.has(adId)) {
                        this.trackImpression(adId);
                        this.viewedAds.add(adId);
                    }
                }
            });
        }, {
            threshold: 0.5, // 50% visibility
            rootMargin: '0px 0px -50px 0px'
        });

        adContainers.forEach(container => {
            observer.observe(container);
        });
    }

    setupClickTracking() {
        document.addEventListener('click', (e) => {
            const adLink = e.target.closest('.ad-link, .ad-overlay-link');
            if (adLink) {
                const container = adLink.closest('.advertisement-container');
                if (container) {
                    const adId = container.dataset.adId;
                    if (adId) {
                        this.trackClick(adId);
                    }
                }
            }
        });
    }

    trackImpression(adId) {
        fetch('/ads/track-impression-ajax/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({
                ad_id: adId,
                page_url: window.location.href,
                timestamp: Date.now()
            })
        }).catch(e => console.log('Impression tracking failed:', e));
    }

    trackClick(adId) {
        if (this.clickedAds.has(adId)) return;
        
        this.clickedAds.add(adId);
        
        fetch('/ads/track-click-ajax/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({
                ad_id: adId,
                page_url: window.location.href,
                timestamp: Date.now()
            })
        }).catch(e => console.log('Click tracking failed:', e));
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.content || '';
    }

    detectAdBlocker() {
        // Simple ad blocker detection
        const testAd = document.createElement('div');
        testAd.innerHTML = '&nbsp;';
        testAd.className = 'adsbox';
        testAd.style.position = 'absolute';
        testAd.style.left = '-10000px';
        document.body.appendChild(testAd);

        setTimeout(() => {
            if (testAd.offsetHeight === 0) {
                this.showAdBlockerMessage();
            }
            document.body.removeChild(testAd);
        }, 100);
    }

    showAdBlockerMessage() {
        const message = document.createElement('div');
        message.className = 'ad-blocker-message';
        message.innerHTML = `
            <p><strong>Ad Blocker Detected</strong></p>
            <p>Please consider disabling your ad blocker to support our content.</p>
        `;
        
        // Insert after header or at top of main content
        const target = document.querySelector('header') || document.querySelector('main');
        if (target) {
            target.insertAdjacentElement('afterend', message);
        }
    }

    loadPopupAds() {
        // Load popup ads after a delay
        setTimeout(() => {
            this.checkForPopupAds();
        }, 10000); // 10 seconds delay
    }

    checkForPopupAds() {
        // Check if user has seen popup recently
        const lastPopup = localStorage.getItem('last_popup_ad');
        const now = Date.now();
        const oneDayMs = 24 * 60 * 60 * 1000;
        
        if (!lastPopup || (now - parseInt(lastPopup)) > oneDayMs) {
            this.showPopupAd();
        }
    }

    showPopupAd() {
        // This would be populated by your backend
        const popupAdData = window.popupAdData;
        if (!popupAdData) return;

        const overlay = document.createElement('div');
        overlay.className = 'ad-popup-overlay';
        overlay.innerHTML = `
            <div class="ad-popup-content">
                <button class="ad-popup-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
                ${popupAdData.content}
            </div>
        `;

        document.body.appendChild(overlay);
        
        // Track impression
        this.trackImpression(popupAdData.id);
        
        // Store timestamp
        localStorage.setItem('last_popup_ad', Date.now().toString());

        // Auto-close after 30 seconds
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.remove();
            }
        }, 30000);
    }

    // Lazy loading for ads
    lazyLoadAds() {
        const lazyAds = document.querySelectorAll('.advertisement-container[data-lazy="true"]');
        
        const lazyObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadAd(entry.target);
                    lazyObserver.unobserve(entry.target);
                }
            });
        });

        lazyAds.forEach(ad => lazyObserver.observe(ad));
    }

    loadAd(container) {
        const adId = container.dataset.adId;
        fetch(`/ads/load/${adId}/`)
            .then(response => response.text())
            .then(html => {
                container.innerHTML = html;
                container.removeAttribute('data-lazy');
            })
            .catch(e => console.log('Failed to load ad:', e));
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.adManager = new AdManager();
});

// Utility functions
function closeStickyAd() {
    const stickyAd = document.getElementById('sticky-ad');
    if (stickyAd) {
        stickyAd.style.display = 'none';
        localStorage.setItem('sticky-ad-closed', 'true');
    }
}

function closePopupAd(element) {
    element.closest('.ad-popup-overlay').remove();
}