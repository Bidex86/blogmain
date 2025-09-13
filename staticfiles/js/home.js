document.addEventListener("DOMContentLoaded", () => {
    // Initialize all features
    initPaginationEnhancements();
    initLazyLoading();
    initScrollAnimations();
    initImageErrorHandling();
    initAccessibilityEnhancements();
    initPerformanceOptimizations();
});

/**
 * Enhance pagination with loading states and smooth transitions
 */
function initPaginationEnhancements() {
    const paginationLinks = document.querySelectorAll('.pagination a');
    
    paginationLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            // Show loading indicator
            showLoadingIndicator();
            
            // Add loading class to body
            document.body.classList.add('loading');
            
            // Remove loading after navigation starts
            setTimeout(() => {
                hideLoadingIndicator();
            }, 1000);
        });
    });
}

/**
 * Implement lazy loading for images
 */
function initLazyLoading() {
    // Only add lazy loading if browser doesn't support native lazy loading
    if ('loading' in HTMLImageElement.prototype) {
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            if (!img.hasAttribute('loading')) {
                img.setAttribute('loading', 'lazy');
            }
        });
    } else {
        // Fallback for older browsers
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    observer.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));
    }
}

/**
 * Add scroll animations for article cards
 */
function initScrollAnimations() {
    const articleCards = document.querySelectorAll('.article-card');
    
    if (articleCards.length === 0) return;
    
    // Set initial state
    articleCards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    });
    
    // Intersection Observer for animations
    const animationObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                // Stagger animations
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, index * 100);
                
                animationObserver.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '50px'
    });

    articleCards.forEach(card => animationObserver.observe(card));
}

/**
 * Handle image loading errors gracefully
 */
function initImageErrorHandling() {
    const images = document.querySelectorAll('img');
    
    images.forEach(img => {
        img.addEventListener('error', function() {
            // Replace broken image with placeholder
            this.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDMwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjRjVGNUY1Ii8+CjxwYXRoIGQ9Ik0xMjUgNzVMMTc1IDEyNUgxMjVWNzVaIiBmaWxsPSIjREREIi8+CjxwYXRoIGQ9Ik0xNzUgNzVMMTI1IDEyNUgxNzVWNzVaIiBmaWxsPSIjREREIi8+Cjx0ZXh0IHg9IjE1MCIgeT0iMTUwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSIjOTk5IiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCI+SW1hZ2UgdW5hdmFpbGFibGU8L3RleHQ+Cjwvc3ZnPg==';
            this.alt = 'Image unavailable';
            this.classList.add('image-error');
        });
        
        // Add loading state
        img.addEventListener('load', function() {
            this.classList.add('image-loaded');
        });
    });
}

/**
 * Enhance accessibility
 */
function initAccessibilityEnhancements() {
    // Add skip links
    addSkipLinks();
    
    // Improve keyboard navigation
    enhanceKeyboardNavigation();
    
    // Add ARIA labels where needed
    addAriaLabels();
}

/**
 * Add skip links for screen readers
 */
function addSkipLinks() {
    const skipLinks = document.createElement('div');
    skipLinks.className = 'skip-links';
    skipLinks.innerHTML = `
        <a href="#main-content" class="skip-link">Skip to main content</a>
        <a href="#navigation" class="skip-link">Skip to navigation</a>
    `;
    
    // Add styles for skip links
    const skipStyles = document.createElement('style');
    skipStyles.textContent = `
        .skip-links {
            position: absolute;
            top: -100px;
            left: 0;
            z-index: 1000;
        }
        .skip-link {
            position: absolute;
            top: -100px;
            left: 0;
            background: #b80000;
            color: white;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 0 0 4px 0;
            font-weight: bold;
        }
        .skip-link:focus {
            top: 0;
        }
    `;
    
    document.head.appendChild(skipStyles);
    document.body.insertBefore(skipLinks, document.body.firstChild);
}

/**
 * Enhance keyboard navigation
 */
function enhanceKeyboardNavigation() {
    const focusableElements = document.querySelectorAll(
        'a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])'
    );
    
    focusableElements.forEach(element => {
        element.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && element.tagName === 'A') {
                element.click();
            }
        });
    });
}

/**
 * Add ARIA labels for better screen reader support
 */
function addAriaLabels() {
    // Add labels to pagination
    const paginationList = document.querySelector('.pagination');
    if (paginationList) {
        paginationList.setAttribute('aria-label', 'Page navigation');
    }
    
    // Add labels to article cards
    const articleCards = document.querySelectorAll('.article-card');
    articleCards.forEach((card, index) => {
        const link = card.querySelector('a');
        if (link && !link.getAttribute('aria-label')) {
            const title = card.querySelector('h4, h5');
            if (title) {
                link.setAttribute('aria-label', `Read article: ${title.textContent.trim()}`);
            }
        }
    });
    
    // Add labels to category sections
    const categoryBlocks = document.querySelectorAll('.category-block');
    categoryBlocks.forEach(block => {
        const heading = block.querySelector('h2');
        if (heading) {
            block.setAttribute('aria-labelledby', `category-${heading.textContent.trim().toLowerCase().replace(/\s+/g, '-')}`);
            heading.id = `category-${heading.textContent.trim().toLowerCase().replace(/\s+/g, '-')}`;
        }
    });
}

/**
 * Performance optimizations
 */
function initPerformanceOptimizations() {
    // Debounce scroll events
    let scrollTimeout;
    window.addEventListener('scroll', () => {
        if (scrollTimeout) {
            clearTimeout(scrollTimeout);
        }
        scrollTimeout = setTimeout(() => {
            // Handle scroll-based functionality here if needed
        }, 16); // ~60fps
    }, { passive: true });
    
    // Preload critical images
    preloadCriticalImages();
    
    // Initialize service worker if available
    initServiceWorker();
}

/**
 * Preload critical images (featured post, trending posts)
 */
function preloadCriticalImages() {
    const criticalImages = document.querySelectorAll('.featured-article img, .trending-post img');
    
    criticalImages.forEach(img => {
        if (img.src && !img.complete) {
            const preloadLink = document.createElement('link');
            preloadLink.rel = 'preload';
            preloadLink.as = 'image';
            preloadLink.href = img.src;
            document.head.appendChild(preloadLink);
        }
    });
}

/**
 * Initialize service worker for caching
 */
function initServiceWorker() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('ServiceWorker registered successfully');
            })
            .catch(error => {
                console.log('ServiceWorker registration failed');
            });
    }
}

/**
 * Show loading indicator
 */
function showLoadingIndicator() {
    const existingIndicator = document.querySelector('.loading-indicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'loading-indicator';
    loadingIndicator.innerHTML = `
        <div class="loading-spinner">
            <div class="spinner"></div>
            <span>Loading...</span>
        </div>
    `;
    
    // Add styles for loading indicator
    const loadingStyles = document.createElement('style');
    loadingStyles.textContent = `
        .loading-indicator {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            backdrop-filter: blur(2px);
        }
        .loading-spinner {
            background: white;
            padding: 2rem;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #b80000;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .loading-spinner span {
            color: #333;
            font-weight: 500;
        }
    `;
    
    if (!document.querySelector('#loading-styles')) {
        loadingStyles.id = 'loading-styles';
        document.head.appendChild(loadingStyles);
    }
    
    document.body.appendChild(loadingIndicator);
}

/**
 * Hide loading indicator
 */
function hideLoadingIndicator() {
    const loadingIndicator = document.querySelector('.loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.style.opacity = '0';
        setTimeout(() => {
            loadingIndicator.remove();
            document.body.classList.remove('loading');
        }, 300);
    }
}

/**
 * Error handling for failed requests
 */
function handleError(error, context = 'general') {
    console.error(`Error in ${context}:`, error);
    
    // Show user-friendly error message
    const errorMessage = document.createElement('div');
    errorMessage.className = 'error-notification';
    errorMessage.innerHTML = `
        <div class="error-content">
            <strong>Oops!</strong> Something went wrong. Please try again.
            <button class="error-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    // Add error notification styles
    const errorStyles = document.createElement('style');
    errorStyles.textContent = `
        .error-notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #f44336;
            color: white;
            padding: 1rem;
            border-radius: 4px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            animation: slideIn 0.3s ease;
        }
        .error-content {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .error-close {
            background: none;
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0;
            width: 24px;
            height: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    `;
    
    if (!document.querySelector('#error-styles')) {
        errorStyles.id = 'error-styles';
        document.head.appendChild(errorStyles);
    }
    
    document.body.appendChild(errorMessage);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (errorMessage.parentNode) {
            errorMessage.remove();
        }
    }, 5000);
}

/**
 * Initialize search functionality (if search input exists)
 */
function initSearchEnhancements() {
    const searchInput = document.querySelector('input[type="search"], .search-input');
    if (!searchInput) return;
    
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }
        
        // Debounce search for performance
        searchTimeout = setTimeout(() => {
            const query = e.target.value.trim();
            if (query.length > 2) {
                // Implement search suggestions or live search here
                console.log('Searching for:', query);
            }
        }, 300);
    });
}

/**
 * Add print styles optimization
 */
function initPrintOptimizations() {
    const printStyles = document.createElement('style');
    printStyles.media = 'print';
    printStyles.textContent = `
        @media print {
            .sidebar, .pagination, .category-sidebar, .category-sidebar-right {
                display: none !important;
            }
            .featured-layout {
                grid-template-columns: 1fr !important;
            }
            .category-layout {
                grid-template-columns: 1fr !important;
            }
            .article-card, .featured-article {
                break-inside: avoid;
            }
            body {
                background: white !important;
                color: black !important;
            }
            a {
                color: black !important;
                text-decoration: underline !important;
            }
        }
    `;
    document.head.appendChild(printStyles);
}

// Initialize additional features
document.addEventListener("DOMContentLoaded", () => {
    initSearchEnhancements();
    initPrintOptimizations();
});