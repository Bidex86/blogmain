/**
 * blog-enhancements.js
 * Additional functionality for the blog post page
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // ========================================
    // READING PROGRESS INDICATOR
    // ========================================
    const progressBar = createProgressBar();
    updateReadingProgress();
    
    function createProgressBar() {
        const progressDiv = document.createElement('div');
        progressDiv.className = 'reading-progress';
        document.body.appendChild(progressDiv);
        return progressDiv;
    }
    
    function updateReadingProgress() {
        const article = document.querySelector('.blog-content');
        if (!article) return;
        
        window.addEventListener('scroll', () => {
            const articleTop = article.offsetTop;
            const articleHeight = article.offsetHeight;
            const windowHeight = window.innerHeight;
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            const articleStart = articleTop - windowHeight / 3;
            const articleEnd = articleTop + articleHeight - windowHeight / 3;
            
            if (scrollTop >= articleStart && scrollTop <= articleEnd) {
                const progress = (scrollTop - articleStart) / (articleEnd - articleStart);
                progressBar.style.width = Math.min(100, Math.max(0, progress * 100)) + '%';
            } else if (scrollTop < articleStart) {
                progressBar.style.width = '0%';
            } else {
                progressBar.style.width = '100%';
            }
        });
    }
    
    // ========================================
    // BACK TO TOP BUTTON
    // ========================================
    const backToTop = createBackToTopButton();
    
    function createBackToTopButton() {
        const button = document.createElement('a');
        button.href = '#';
        button.className = 'back-to-top';
        button.innerHTML = '↑';
        button.setAttribute('aria-label', 'Back to top');
        button.title = 'Back to top';
        
        button.addEventListener('click', (e) => {
            e.preventDefault();
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
        
        document.body.appendChild(button);
        return button;
    }
    
    // Show/hide back to top button
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 300) {
            backToTop.classList.add('visible');
        } else {
            backToTop.classList.remove('visible');
        }
    });
    
    // ========================================
    // TABLE OF CONTENTS GENERATOR
    // ========================================
    generateTableOfContents();
    
    function generateTableOfContents() {
        const headings = document.querySelectorAll('.post-body h2, .post-body h3');
        if (headings.length < 3) return; // Don't show TOC for short articles
        
        const sidebar = document.querySelector('.blog-sidebar');
        if (!sidebar) return;
        
        const tocSection = document.createElement('section');
        tocSection.className = 'table-of-contents';
        
        const tocTitle = document.createElement('h4');
        tocTitle.textContent = 'Table of Contents';
        tocSection.appendChild(tocTitle);
        
        const tocList = document.createElement('ul');
        tocList.className = 'toc-list';
        
        headings.forEach((heading, index) => {
            // Add ID to heading if it doesn't have one
            if (!heading.id) {
                heading.id = `heading-${index}`;
            }
            
            const li = document.createElement('li');
            const link = document.createElement('a');
            link.href = `#${heading.id}`;
            link.textContent = heading.textContent;
            link.style.paddingLeft = heading.tagName === 'H3' ? '15px' : '0';
            
            // Smooth scroll to heading
            link.addEventListener('click', (e) => {
                e.preventDefault();
                heading.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                
                // Update active link
                document.querySelectorAll('.toc-list a').forEach(a => a.classList.remove('active'));
                link.classList.add('active');
            });
            
            li.appendChild(link);
            tocList.appendChild(li);
        });
        
        tocSection.appendChild(tocList);
        sidebar.insertBefore(tocSection, sidebar.firstChild);
        
        // Highlight current section in TOC while scrolling
        window.addEventListener('scroll', updateTOCActive);
    }
    
    function updateTOCActive() {
        const headings = document.querySelectorAll('.post-body h2, .post-body h3');
        const tocLinks = document.querySelectorAll('.toc-list a');
        
        let current = null;
        headings.forEach((heading, index) => {
            const rect = heading.getBoundingClientRect();
            if (rect.top <= 100) {
                current = index;
            }
        });
        
        tocLinks.forEach((link, index) => {
            link.classList.toggle('active', index === current);
        });
    }
    
    // ========================================
    // SOCIAL SHARE ENHANCEMENTS
    // ========================================
    enhanceSocialSharing();
    
    function enhanceSocialSharing() {
        const shareButtons = document.querySelectorAll('.share-btn');
        
        shareButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                // Add click tracking (you can integrate with analytics)
                const platform = button.className.split(' ').find(cls => 
                    ['facebook', 'twitter', 'linkedin', 'whatsapp'].includes(cls)
                );
                
                console.log(`Shared on ${platform}`);
                
                // Add visual feedback
                const originalText = button.innerHTML;
                button.innerHTML = button.innerHTML.replace(/\w+$/, 'Shared!');
                
                setTimeout(() => {
                    button.innerHTML = originalText;
                }, 2000);
            });
        });
        
        // Add copy link functionality
        addCopyLinkButton();
    }
    
    function addCopyLinkButton() {
        const shareButtons = document.querySelector('.share-buttons');
        if (!shareButtons) return;
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'share-btn copy-link';
        copyBtn.innerHTML = '<i class="fas fa-link"></i> Copy Link';
        copyBtn.style.background = '#6c757d';
        copyBtn.style.color = 'white';
        copyBtn.style.border = 'none';
        
        copyBtn.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(window.location.href);
                const originalText = copyBtn.innerHTML;
                copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                copyBtn.style.background = '#28a745';
                
                setTimeout(() => {
                    copyBtn.innerHTML = originalText;
                    copyBtn.style.background = '#6c757d';
                }, 2000);
            } catch (err) {
                // Fallback for browsers that don't support clipboard API
                const textArea = document.createElement('textarea');
                textArea.value = window.location.href;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                
                const originalText = copyBtn.innerHTML;
                copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                copyBtn.style.background = '#28a745';
                
                setTimeout(() => {
                    copyBtn.innerHTML = originalText;
                    copyBtn.style.background = '#6c757d';
                }, 2000);
            }
        });
        
        shareButtons.appendChild(copyBtn);
    }
    
    // ========================================
    // IMAGE ENHANCEMENTS
    // ========================================
    enhanceImages();
    
    function enhanceImages() {
        const images = document.querySelectorAll('.post-body img');
        
        images.forEach((img, index) => {
            // Add loading animation
            img.style.opacity = '0';
            img.style.transition = 'opacity 0.3s ease';
            
            img.addEventListener('load', () => {
                img.style.opacity = '1';
            });
            
            // Add lightbox functionality
            img.style.cursor = 'zoom-in';
            img.addEventListener('click', () => {
                openLightbox(img, index, images);
            });
            
            // Add lazy loading for images below the fold
            if (img.getBoundingClientRect().top > window.innerHeight) {
                img.loading = 'lazy';
            }
        });
    }
    
    function openLightbox(img, currentIndex, allImages) {
        const lightbox = document.createElement('div');
        lightbox.className = 'lightbox';
        lightbox.innerHTML = `
            <div class="lightbox-content">
                <img src="${img.src}" alt="${img.alt || 'Image'}" class="lightbox-img">
                <div class="lightbox-controls">
                    <button class="lightbox-prev" aria-label="Previous image">‹</button>
                    <button class="lightbox-next" aria-label="Next image">›</button>
                    <button class="lightbox-close" aria-label="Close lightbox">×</button>
                </div>
                <div class="lightbox-counter">${currentIndex + 1} / ${allImages.length}</div>
            </div>
        `;
        
        // Add lightbox styles
        const style = document.createElement('style');
        style.textContent = `
            .lightbox {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.9);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                animation: fadeIn 0.3s ease;
            }
            .lightbox-content {
                position: relative;
                max-width: 90%;
                max-height: 90%;
            }
            .lightbox-img {
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
            }
            .lightbox-controls {
                position: absolute;
                top: 20px;
                right: 20px;
                display: flex;
                gap: 10px;
            }
            .lightbox-controls button {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                cursor: pointer;
                font-size: 18px;
                transition: background 0.2s ease;
            }
            .lightbox-controls button:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            .lightbox-prev, .lightbox-next {
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                font-size: 30px;
                width: 50px;
                height: 50px;
            }
            .lightbox-prev {
                left: 20px;
            }
            .lightbox-next {
                right: 20px;
            }
            .lightbox-counter {
                position: absolute;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                color: white;
                background: rgba(0, 0, 0, 0.5);
                padding: 5px 15px;
                border-radius: 15px;
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(lightbox);
        
        let current = currentIndex;
        
        // Navigation functions
        function showImage(index) {
            const lightboxImg = lightbox.querySelector('.lightbox-img');
            const counter = lightbox.querySelector('.lightbox-counter');
            lightboxImg.src = allImages[index].src;
            lightboxImg.alt = allImages[index].alt || 'Image';
            counter.textContent = `${index + 1} / ${allImages.length}`;
            current = index;
        }
        
        // Event listeners
        lightbox.querySelector('.lightbox-close').addEventListener('click', () => {
            lightbox.remove();
            style.remove();
        });
        
        lightbox.querySelector('.lightbox-prev').addEventListener('click', () => {
            current = (current - 1 + allImages.length) % allImages.length;
            showImage(current);
        });
        
        lightbox.querySelector('.lightbox-next').addEventListener('click', () => {
            current = (current + 1) % allImages.length;
            showImage(current);
        });
        
        // Keyboard navigation
        document.addEventListener('keydown', function handleKeydown(e) {
            if (e.key === 'Escape') {
                lightbox.remove();
                style.remove();
                document.removeEventListener('keydown', handleKeydown);
            } else if (e.key === 'ArrowLeft') {
                lightbox.querySelector('.lightbox-prev').click();
            } else if (e.key === 'ArrowRight') {
                lightbox.querySelector('.lightbox-next').click();
            }
        });
        
        // Close on background click
        lightbox.addEventListener('click', (e) => {
            if (e.target === lightbox) {
                lightbox.remove();
                style.remove();
            }
        });
    }
    
    // ========================================
    // TEXT SELECTION SHARING
    // ========================================
    enableTextSelectionSharing();
    
    function enableTextSelectionSharing() {
        let selectionTimeout;
        
        document.addEventListener('mouseup', () => {
            clearTimeout(selectionTimeout);
            selectionTimeout = setTimeout(() => {
                const selection = window.getSelection();
                const selectedText = selection.toString().trim();
                
                if (selectedText.length > 10 && selectedText.length < 280) {
                    showSelectionTooltip(selection, selectedText);
                } else {
                    hideSelectionTooltip();
                }
            }, 100);
        });
        
        document.addEventListener('mousedown', hideSelectionTooltip);
    }
    
    function showSelectionTooltip(selection, text) {
        hideSelectionTooltip(); // Remove any existing tooltip
        
        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        
        const tooltip = document.createElement('div');
        tooltip.className = 'selection-tooltip';
        tooltip.innerHTML = `
            <button class="selection-share-btn twitter" data-platform="twitter">
                <i class="fab fa-twitter"></i>
            </button>
            <button class="selection-share-btn facebook" data-platform="facebook">
                <i class="fab fa-facebook-f"></i>
            </button>
            <button class="selection-share-btn copy" data-platform="copy">
                <i class="fas fa-copy"></i>
            </button>
        `;
        
        // Add tooltip styles
        const style = document.createElement('style');
        style.id = 'selection-tooltip-style';
        style.textContent = `
            .selection-tooltip {
                position: absolute;
                background: #333;
                border-radius: 20px;
                padding: 5px;
                display: flex;
                gap: 5px;
                z-index: 1000;
                animation: fadeIn 0.2s ease;
            }
            .selection-share-btn {
                background: transparent;
                border: none;
                color: white;
                width: 30px;
                height: 30px;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.2s ease;
            }
            .selection-share-btn:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            .selection-share-btn.twitter:hover { background: #1da1f2; }
            .selection-share-btn.facebook:hover { background: #1877f2; }
            .selection-share-btn.copy:hover { background: #28a745; }
        `;
        document.head.appendChild(style);
        
        tooltip.style.left = rect.left + (rect.width / 2) - 50 + 'px';
        tooltip.style.top = rect.top - 50 + window.scrollY + 'px';
        
        document.body.appendChild(tooltip);
        
        // Add event listeners
        tooltip.querySelectorAll('.selection-share-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const platform = btn.dataset.platform;
                const pageUrl = encodeURIComponent(window.location.href);
                const selectedText = encodeURIComponent(`"${text}"`);
                
                switch (platform) {
                    case 'twitter':
                        window.open(`https://twitter.com/intent/tweet?text=${selectedText}&url=${pageUrl}`, '_blank');
                        break;
                    case 'facebook':
                        window.open(`https://www.facebook.com/sharer/sharer.php?u=${pageUrl}&quote=${selectedText}`, '_blank');
                        break;
                    case 'copy':
                        navigator.clipboard.writeText(text).then(() => {
                            btn.innerHTML = '<i class="fas fa-check"></i>';
                            setTimeout(() => {
                                btn.innerHTML = '<i class="fas fa-copy"></i>';
                            }, 1000);
                        });
                        break;
                }
            });
        });
    }
    
    function hideSelectionTooltip() {
        const tooltip = document.querySelector('.selection-tooltip');
        const style = document.getElementById('selection-tooltip-style');
        if (tooltip) tooltip.remove();
        if (style) style.remove();
    }
    
    // ========================================
    // ESTIMATED READING TIME
    // ========================================
    updateReadingTime();
    
    function updateReadingTime() {
        const content = document.querySelector('.post-body');
        if (!content) return;
        
        const text = content.textContent || content.innerText;
        const wordsPerMinute = 200;
        const wordCount = text.trim().split(/\s+/).length;
        const readingTime = Math.ceil(wordCount / wordsPerMinute);
        
        // Update existing reading time display
        const readingTimeElement = document.querySelector('.reading-time');
        if (readingTimeElement) {
            readingTimeElement.textContent = `${readingTime} min read`;
        }
        
        // Add word count display
        const wordCountElement = document.querySelector('.word-count');
        if (wordCountElement) {
            wordCountElement.textContent = `${wordCount.toLocaleString()} words`;
        }
    }
    
    // ========================================
    // ACCESSIBILITY ENHANCEMENTS
    // ========================================
    enhanceAccessibility();
    
    function enhanceAccessibility() {
        // Add skip link
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Skip to main content';
        skipLink.className = 'sr-only';
        skipLink.style.cssText = `
            position: absolute;
            left: -9999px;
            z-index: 999;
            padding: 1em;
            background: #000;
            color: white;
            text-decoration: none;
        `;
        
        skipLink.addEventListener('focus', () => {
            skipLink.style.left = '6px';
            skipLink.style.top = '7px';
        });
        
        skipLink.addEventListener('blur', () => {
            skipLink.style.left = '-9999px';
        });
        
        document.body.insertBefore(skipLink, document.body.firstChild);
        
        // Add main content ID if it doesn't exist
        const mainContent = document.querySelector('.blog-main');
        if (mainContent && !mainContent.id) {
            mainContent.id = 'main-content';
        }
        
        // Enhance focus indicators
        const focusableElements = document.querySelectorAll('a, button, input, textarea, select');
        focusableElements.forEach(element => {
            element.addEventListener('focus', () => {
                element.style.outline = '2px solid #007bff';
                element.style.outlineOffset = '2px';
            });
            
            element.addEventListener('blur', () => {
                element.style.outline = '';
                element.style.outlineOffset = '';
            });
        });
    }
    
    // ========================================
    // PERFORMANCE MONITORING
    // ========================================
    monitorPerformance();
    
    function monitorPerformance() {
        // Monitor Core Web Vitals
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    if (entry.entryType === 'largest-contentful-paint') {
                        console.log('LCP:', entry.startTime);
                    }
                    
                    if (entry.entryType === 'first-input') {
                        console.log('FID:', entry.processingStart - entry.startTime);
                    }
                    
                    if (entry.entryType === 'layout-shift') {
                        if (!entry.hadRecentInput) {
                            console.log('CLS:', entry.value);
                        }
                    }
                }
            });
            
            observer.observe({ entryTypes: ['largest-contentful-paint', 'first-input', 'layout-shift'] });
        }
        
        // Log page load time
        window.addEventListener('load', () => {
            const loadTime = performance.now();
            console.log(`Page loaded in ${loadTime.toFixed(2)}ms`);
        });
    }
    
    // ========================================
    // KEYBOARD SHORTCUTS
    // ========================================
    addKeyboardShortcuts();
    
    function addKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Only activate shortcuts when not typing in inputs
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            switch (e.key) {
                case 'c':
                    // Focus on comment form
                    const commentTextarea = document.querySelector('textarea[name="comment"]');
                    if (commentTextarea) {
                        commentTextarea.focus();
                        commentTextarea.scrollIntoView({ behavior: 'smooth' });
                    }
                    break;
                    
                case 's':
                    // Focus on search (if available)
                    const searchInput = document.querySelector('.search-input');
                    if (searchInput) {
                        searchInput.focus();
                    }
                    break;
                    
                case 't':
                    // Scroll to top
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                    break;
                    
                case 'b':
                    // Scroll to bottom
                    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
                    break;
            }
        });
        
        // Show keyboard shortcuts help
        const helpButton = document.createElement('button');
        helpButton.innerHTML = '?';
        helpButton.title = 'Keyboard shortcuts';
        helpButton.style.cssText = `
            position: fixed;
            bottom: 30px;
            left: 30px;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #6c757d;
            color: white;
            border: none;
            cursor: pointer;
            z-index: 1000;
            font-size: 18px;
        `;
        
        helpButton.addEventListener('click', showKeyboardHelp);
        document.body.appendChild(helpButton);
    }
    
    function showKeyboardHelp() {
        const helpModal = document.createElement('div');
        helpModal.innerHTML = `
            <div class="help-modal">
                <div class="help-content">
                    <h3>Keyboard Shortcuts</h3>
                    <div class="shortcut-list">
                        <div class="shortcut-item">
                            <kbd>C</kbd>
                            <span>Focus comment form</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>S</kbd>
                            <span>Focus search</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>T</kbd>
                            <span>Scroll to top</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>B</kbd>
                            <span>Scroll to bottom</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>Esc</kbd>
                            <span>Close modal/Cancel reply</span>
                        </div>
                        <div class="shortcut-item">
                            <kbd>←/→</kbd>
                            <span>Navigate lightbox images</span>
                        </div>
                    </div>
                    <button class="close-help">Close</button>
                </div>
            </div>
        `;
        
        // Add modal styles
        const style = document.createElement('style');
        style.textContent = `
            .help-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10001;
                animation: fadeIn 0.3s ease;
            }
            .help-content {
                background: white;
                padding: 30px;
                border-radius: 10px;
                max-width: 400px;
                width: 90%;
            }
            .help-content h3 {
                margin: 0 0 20px 0;
                text-align: center;
            }
            .shortcut-list {
                display: flex;
                flex-direction: column;
                gap: 10px;
                margin-bottom: 20px;
            }
            .shortcut-item {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            .shortcut-item kbd {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 3px;
                padding: 3px 8px;
                font-family: monospace;
                font-size: 0.9em;
                min-width: 30px;
                text-align: center;
            }
            .close-help {
                width: 100%;
                padding: 10px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1em;
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(helpModal);
        
        // Close modal functionality
        const closeHelp = () => {
            helpModal.remove();
            style.remove();
        };
        
        helpModal.querySelector('.close-help').addEventListener('click', closeHelp);
        helpModal.addEventListener('click', (e) => {
            if (e.target === helpModal) closeHelp();
        });
        
        document.addEventListener('keydown', function handleEscape(e) {
            if (e.key === 'Escape') {
                closeHelp();
                document.removeEventListener('keydown', handleEscape);
            }
        });
    }
    
    // ========================================
    // ANALYTICS INTEGRATION
    // ========================================
    trackUserInteractions();
    
    function trackUserInteractions() {
        // Track reading progress milestones
        let milestones = [25, 50, 75, 100];
        let trackedMilestones = [];
        
        window.addEventListener('scroll', () => {
            const scrollPercent = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100;
            
            milestones.forEach(milestone => {
                if (scrollPercent >= milestone && !trackedMilestones.includes(milestone)) {
                    trackedMilestones.push(milestone);
                    
                    // Send to analytics (replace with your analytics service)
                    console.log(`Reading progress: ${milestone}%`);
                    
                    // Example: Google Analytics 4
                    if (typeof gtag !== 'undefined') {
                        gtag('event', 'scroll_progress', {
                            event_category: 'engagement',
                            event_label: `${milestone}%`,
                            value: milestone
                        });
                    }
                }
            });
        });
        
        // Track time spent on page
        let startTime = Date.now();
        
        window.addEventListener('beforeunload', () => {
            const timeSpent = Math.round((Date.now() - startTime) / 1000);
            
            console.log(`Time spent: ${timeSpent} seconds`);
            
            // Send to analytics
            if (typeof gtag !== 'undefined') {
                gtag('event', 'time_on_page', {
                    event_category: 'engagement',
                    event_label: window.location.pathname,
                    value: timeSpent
                });
            }
        });
        
        // Track outbound links
        document.querySelectorAll('a[href^="http"]:not([href*="' + window.location.hostname + '"])').forEach(link => {
            link.addEventListener('click', () => {
                console.log(`Outbound link clicked: ${link.href}`);
                
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'outbound_link', {
                        event_category: 'engagement',
                        event_label: link.href,
                        transport_type: 'beacon'
                    });
                }
            });
        });
    }
});

// ========================================
// UTILITY FUNCTIONS
// ========================================

// Throttle function for performance
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Debounce function for performance
function debounce(func, wait, immediate) {
    let timeout;
    return function() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}