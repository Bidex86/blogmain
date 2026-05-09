// Comment Form Handler - Prevents multiple submissions
document.addEventListener('DOMContentLoaded', function() {
    let isSubmitting = false;
    
    // Get all comment forms
    const commentForms = document.querySelectorAll('form[action*="comment"]');
    
    commentForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Prevent multiple submissions
            if (isSubmitting) {
                e.preventDefault();
                console.log('Already submitting...');
                return false;
            }
            
            const submitBtn = form.querySelector('button[type="submit"]');
            const textarea = form.querySelector('textarea[name="comment"]');
            
            // Validate
            if (!textarea || !textarea.value.trim()) {
                e.preventDefault();
                alert('Please enter a comment');
                return false;
            }
            
            // Mark as submitting
            isSubmitting = true;
            
            // Disable button
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.dataset.originalText = submitBtn.textContent;
                submitBtn.textContent = 'Posting...';
            }
            
            // Re-enable after 5 seconds (safety timeout)
            setTimeout(() => {
                isSubmitting = false;
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = submitBtn.dataset.originalText || 'Post Comment';
                }
            }, 5000);
        });
    });
});