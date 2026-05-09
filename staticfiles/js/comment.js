// static/js/comment.js - FIXED: Prevents double-click and race conditions

document.addEventListener('DOMContentLoaded', function() {
    
    // Get CSRF token
    function getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
    
    // Track pending requests to prevent double-clicks
    const pendingLikeRequests = new Set();
    
    // Character counter for all textareas
    const textareas = document.querySelectorAll('.comment-textarea, .reply-textarea');
    textareas.forEach(textarea => {
        const maxLength = parseInt(textarea.getAttribute('maxlength')) || 1000;
        const counterElement = textarea.closest('.form-group')?.querySelector('.character-count') || 
                              textarea.parentElement?.querySelector('.character-count');
        
        if (counterElement) {
            updateCounter(textarea, counterElement, maxLength);
            textarea.addEventListener('input', function() {
                updateCounter(this, counterElement, maxLength);
            });
        }
        
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });
    
    function updateCounter(textarea, counter, maxLength) {
        const currentLength = textarea.value.length;
        counter.textContent = `${currentLength}/${maxLength}`;
        
        if (currentLength > maxLength * 0.9) {
            counter.style.color = '#dc3545';
            counter.style.fontWeight = '600';
        } else {
            counter.style.color = '#6c757d';
            counter.style.fontWeight = 'normal';
        }
    }
    
    // Reply button functionality
    document.addEventListener('click', function(e) {
        if (e.target.closest('.reply-btn')) {
            e.preventDefault();
            const btn = e.target.closest('.reply-btn');
            const commentId = btn.getAttribute('data-comment-id');
            const replyForm = document.getElementById(`reply-form-${commentId}`);
            
            if (replyForm) {
                document.querySelectorAll('.reply-form-container').forEach(form => {
                    if (form.id !== `reply-form-${commentId}`) {
                        form.style.display = 'none';
                    }
                });
                
                if (replyForm.style.display === 'none' || !replyForm.style.display) {
                    replyForm.style.display = 'block';
                    const textarea = replyForm.querySelector('textarea');
                    if (textarea) {
                        textarea.focus();
                        replyForm.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }
                } else {
                    replyForm.style.display = 'none';
                }
            }
        }
    });
    
    // Cancel reply button
    document.addEventListener('click', function(e) {
        if (e.target.closest('.cancel-reply')) {
            e.preventDefault();
            const form = e.target.closest('.reply-form-container');
            if (form) {
                form.style.display = 'none';
                const textarea = form.querySelector('textarea');
                if (textarea) {
                    textarea.value = '';
                }
            }
        }
    });
    
    // Flag button functionality
    document.addEventListener('click', function(e) {
        if (e.target.closest('.flag-btn')) {
            e.preventDefault();
            const btn = e.target.closest('.flag-btn');
            const commentId = btn.getAttribute('data-comment-id');
            const flagForm = document.getElementById(`flag-form-${commentId}`);
            
            if (flagForm) {
                document.querySelectorAll('.flag-form-container').forEach(form => {
                    if (form.id !== `flag-form-${commentId}`) {
                        form.style.display = 'none';
                    }
                });
                
                if (flagForm.style.display === 'none' || !flagForm.style.display) {
                    flagForm.style.display = 'block';
                    flagForm.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                } else {
                    flagForm.style.display = 'none';
                }
            }
        }
    });
    
    // Cancel flag button
    document.addEventListener('click', function(e) {
        if (e.target.closest('.cancel-flag')) {
            e.preventDefault();
            const form = e.target.closest('.flag-form-container');
            if (form) {
                form.style.display = 'none';
            }
        }
    });
    
    // Like button with AJAX - FIXED: Prevents double-clicks and race conditions
    document.addEventListener('submit', function(e) {
        if (e.target.classList.contains('like-form')) {
            e.preventDefault();
            e.stopImmediatePropagation(); // Prevent multiple handlers
            
            const form = e.target;
            const formAction = form.action;
            
            // Prevent duplicate requests
            if (pendingLikeRequests.has(formAction)) {
                console.log('Like request already in progress, ignoring...');
                return;
            }
            
            const button = form.querySelector('.btn-like');
            const likeCount = form.querySelector('.like-count');
            
            if (!button || !likeCount) {
                console.error('Like button or count element not found');
                return;
            }
            
            // Disable button and mark as pending
            button.disabled = true;
            pendingLikeRequests.add(formAction);
            
            // Visual feedback
            const originalButtonHTML = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            
            fetch(formAction, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': getCSRFToken()
                },
                body: new FormData(form),
                credentials: 'same-origin',
                cache: 'no-store'  // Don't cache this request
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Update count immediately
                    likeCount.textContent = data.like_count;
                    likeCount.setAttribute('data-count', data.like_count);
                    
                    // Update button state
                    if (data.liked) {
                        button.classList.add('liked');
                        button.setAttribute('aria-pressed', 'true');
                    } else {
                        button.classList.remove('liked');
                        button.setAttribute('aria-pressed', 'false');
                    }
                    
                    // Restore button HTML
                    button.innerHTML = originalButtonHTML;
                    
                    console.log('Like updated successfully:', data);
                } else {
                    console.error('Like failed:', data);
                    button.innerHTML = originalButtonHTML;
                }
            })
            .catch(error => {
                console.error('Like request error:', error);
                button.innerHTML = originalButtonHTML;
                alert('Failed to update like. Please try again.');
            })
            .finally(() => {
                // Re-enable button after delay to prevent rapid clicking
                setTimeout(() => {
                    button.disabled = false;
                    pendingLikeRequests.delete(formAction);
                }, 500);
            });
        }
    });
    
    // Delete comment confirmation
    document.addEventListener('submit', function(e) {
        if (e.target.classList.contains('delete-form')) {
            if (!confirm('Are you sure you want to delete this comment? This action cannot be undone.')) {
                e.preventDefault();
                return false;
            }
        }
    });
    
    // Smooth scroll to comments
    const commentLinks = document.querySelectorAll('a[href*="#comment"]');
    commentLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href.includes('#')) {
                const targetId = href.split('#')[1];
                const target = document.getElementById(targetId);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    
                    target.style.transition = 'background-color 0.3s';
                    const originalBg = window.getComputedStyle(target).backgroundColor;
                    target.style.backgroundColor = '#fff3cd';
                    setTimeout(() => {
                        target.style.backgroundColor = originalBg;
                    }, 2000);
                }
            }
        });
    });
    
    // Handle success messages from Django
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            if (!alert.classList.contains('alert-permanent')) {
                setTimeout(() => {
                    alert.style.transition = 'opacity 0.5s';
                    alert.style.opacity = '0';
                    setTimeout(() => {
                        alert.remove();
                    }, 500);
                }, 5000);
            }
        });
    }, 100);
});

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} comment-toast`;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        animation: slideIn 0.3s ease-out;
    `;
    toast.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <span>${message}</span>
            <button type="button" class="btn-close ms-2" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 300);
    }, 5000);
}

// Add animation styles
if (!document.getElementById('comment-animations')) {
    const style = document.createElement('style');
    style.id = 'comment-animations';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
        
        .comment-toast {
            animation: slideIn 0.3s ease-out;
        }
        
        .fa-spin {
            animation: fa-spin 1s infinite linear;
        }
        
        @keyframes fa-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
}
