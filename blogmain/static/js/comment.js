// static/js/comment.js - Enhanced comment functionality
document.addEventListener('DOMContentLoaded', function() {
    
    // Character counter for comment textareas
    function setupCharacterCounter() {
        const textareas = document.querySelectorAll('.comment-textarea, .reply-textarea');
        textareas.forEach(textarea => {
            const counter = textarea.parentElement.querySelector('.character-count');
            if (counter) {
                textarea.addEventListener('input', function() {
                    const current = this.value.length;
                    const max = this.getAttribute('maxlength') || 1000;
                    counter.textContent = `${current}/${max}`;
                    
                    if (current > max * 0.9) {
                        counter.style.color = '#dc3545';
                    } else {
                        counter.style.color = '#6c757d';
                    }
                });
            }
        });
    }
    
    // Auto-resize textareas
    function setupAutoResize() {
        const textareas = document.querySelectorAll('[data-auto-resize="true"], .comment-textarea, .reply-textarea');
        textareas.forEach(textarea => {
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = this.scrollHeight + 'px';
            });
        });
    }
    
    // Reply button functionality
    function setupReplyButtons() {
        document.querySelectorAll('.reply-btn').forEach(button => {
            button.addEventListener('click', function() {
                const commentId = this.dataset.commentId;
                const replyForm = document.getElementById(`reply-form-${commentId}`);
                const allReplyForms = document.querySelectorAll('.reply-form-container');
                
                // Hide all other reply forms
                allReplyForms.forEach(form => {
                    if (form.id !== `reply-form-${commentId}`) {
                        form.style.display = 'none';
                    }
                });
                
                // Toggle current reply form
                if (replyForm) {
                    replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';
                    if (replyForm.style.display === 'block') {
                        const textarea = replyForm.querySelector('textarea');
                        if (textarea) {
                            textarea.focus();
                        }
                    }
                }
            });
        });
    }
    
    // Cancel reply functionality
    function setupCancelButtons() {
        document.querySelectorAll('.cancel-reply').forEach(button => {
            button.addEventListener('click', function() {
                const replyForm = this.closest('.reply-form-container');
                if (replyForm) {
                    replyForm.style.display = 'none';
                    const textarea = replyForm.querySelector('textarea');
                    if (textarea) {
                        textarea.value = '';
                    }
                }
            });
        });
    }
    
    // Flag button functionality
    function setupFlagButtons() {
        document.querySelectorAll('.flag-btn').forEach(button => {
            button.addEventListener('click', function() {
                const commentId = this.dataset.commentId;
                const flagForm = document.getElementById(`flag-form-${commentId}`);
                const allFlagForms = document.querySelectorAll('.flag-form-container');
                
                // Hide all other flag forms
                allFlagForms.forEach(form => {
                    if (form.id !== `flag-form-${commentId}`) {
                        form.style.display = 'none';
                    }
                });
                
                // Toggle current flag form
                if (flagForm) {
                    flagForm.style.display = flagForm.style.display === 'none' ? 'block' : 'none';
                }
            });
        });
        
        // Cancel flag functionality
        document.querySelectorAll('.cancel-flag').forEach(button => {
            button.addEventListener('click', function() {
                const flagForm = this.closest('.flag-form-container');
                if (flagForm) {
                    flagForm.style.display = 'none';
                }
            });
        });
    }
    
    // AJAX like functionality
    function setupLikeFunctionality() {
        document.querySelectorAll('.like-form').forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const button = this.querySelector('.btn-like');
                const likeCount = button.querySelector('.like-count');
                
                fetch(this.action, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        likeCount.textContent = data.like_count;
                        if (data.liked) {
                            button.classList.add('liked');
                        } else {
                            button.classList.remove('liked');
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                });
            });
        });
    }
    
    // AJAX form submission for comments
    function setupAjaxComments() {
        const commentForms = document.querySelectorAll('.comment-form, .reply-form');
        commentForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const submitButton = this.querySelector('button[type="submit"]');
                const originalText = submitButton.innerHTML;
                
                // Show loading state
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Posting...';
                submitButton.disabled = true;
                
                fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Reset form
                        this.reset();
                        
                        // Hide reply form if it's a reply
                        if (this.classList.contains('reply-form')) {
                            this.closest('.reply-form-container').style.display = 'none';
                        }
                        
                        // Reload comments section or add new comment dynamically
                        if (data.comment_html) {
                            const commentsList = document.getElementById('comments-list');
                            if (commentsList) {
                                const tempDiv = document.createElement('div');
                                tempDiv.innerHTML = data.comment_html;
                                const newComment = tempDiv.firstElementChild;
                                
                                if (this.classList.contains('reply-form')) {
                                    // Insert reply after parent comment
                                    const parentId = formData.get('parent_id');
                                    const parentComment = document.querySelector(`[data-comment-id="${parentId}"]`);
                                    if (parentComment) {
                                        let repliesContainer = parentComment.querySelector('.comment-replies');
                                        if (!repliesContainer) {
                                            repliesContainer = document.createElement('div');
                                            repliesContainer.className = 'comment-replies';
                                            parentComment.appendChild(repliesContainer);
                                        }
                                        repliesContainer.appendChild(newComment);
                                    }
                                } else {
                                    // Insert new top-level comment at the beginning
                                    commentsList.insertBefore(newComment, commentsList.firstChild);
                                }
                                
                                // Re-setup event handlers for new comment
                                setupEventHandlers();
                                
                                // Scroll to new comment
                                newComment.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                            }
                        }
                        
                        // Update comment count
                        const commentCount = document.querySelector('.comment-count');
                        if (commentCount) {
                            const currentCount = parseInt(commentCount.textContent.match(/\d+/)[0]);
                            commentCount.textContent = `(${currentCount + 1})`;
                        }
                        
                        // Show success message
                        showMessage(data.message, 'success');
                    } else {
                        // Show error messages
                        if (data.errors) {
                            data.errors.forEach(error => showMessage(error, 'error'));
                        } else if (data.error) {
                            showMessage(data.error, 'error');
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showMessage('An error occurred. Please try again.', 'error');
                })
                .finally(() => {
                    // Reset button state
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                });
            });
        });
    }
    
    // Show notification messages
    function showMessage(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show`;
        messageDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert message at top of comments section
        const commentsSection = document.getElementById('comments');
        if (commentsSection) {
            commentsSection.insertBefore(messageDiv, commentsSection.firstChild);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                messageDiv.remove();
            }, 5000);
        }
    }
    
    // Setup all event handlers
    function setupEventHandlers() {
        setupCharacterCounter();
        setupAutoResize();
        setupReplyButtons();
        setupCancelButtons();
        setupFlagButtons();
        setupLikeFunctionality();
    }
    
    // Initialize everything
    setupEventHandlers();
    setupAjaxComments();
    
    // Comment search functionality (if search box exists)
    const searchInput = document.getElementById('comment-search');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length < 2) {
                document.getElementById('search-results').innerHTML = '';
                return;
            }
            
            searchTimeout = setTimeout(() => {
                const contentTypeId = document.querySelector('[name="content_type_id"]').value;
                const objectId = document.querySelector('[name="object_id"]').value;
                
                fetch(`/comments/api/search/?q=${encodeURIComponent(query)}&content_type_id=${contentTypeId}&object_id=${objectId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displaySearchResults(data.results);
                    }
                })
                .catch(error => console.error('Search error:', error));
            }, 300);
        });
    }
    
    function displaySearchResults(results) {
        const resultsContainer = document.getElementById('search-results');
        if (!resultsContainer) return;
        
        if (results.length === 0) {
            resultsContainer.innerHTML = '<p>No comments found.</p>';
            return;
        }
        
        const html = results.map(result => `
            <div class="search-result">
                <strong>${result.author}</strong> 
                <small>${new Date(result.created_at).toLocaleDateString()}</small>
                <p>${result.content}</p>
            </div>
        `).join('');
        
        resultsContainer.innerHTML = html;
    }
});