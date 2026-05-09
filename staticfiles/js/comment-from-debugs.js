// DIAGNOSTIC COMMENT FORM HANDLER
// Add this to your comment form JavaScript to see what's happening

// Place this in your main comment form submit handler
$('#comment-form').on('submit', function(e) {
    e.preventDefault();
    
    const form = $(this);
    const submitBtn = form.find('button[type="submit"]');
    const formData = new FormData(this);
    
    // Disable submit button
    submitBtn.prop('disabled', true).text('Posting...');
    
    // Log what we're sending
    console.log('=== COMMENT SUBMISSION DEBUG ===');
    console.log('Form data:', Object.fromEntries(formData));
    
    $.ajax({
        url: form.attr('action'),
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        },
        success: function(response) {
            console.log('=== SUCCESS RESPONSE ===');
            console.log('Full response:', response);
            console.log('Success flag:', response.success);
            console.log('Message:', response.message);
            console.log('Comment ID:', response.comment_id);
            
            // Check if response indicates success
            if (response.success === true) {
                console.log('✓ Comment saved successfully!');
                
                // Check if we need to reload
                if (response.reload) {
                    console.log('Reloading page...');
                    location.reload();
                    return;
                }
                
                // Check if we have HTML to insert
                if (response.html) {
                    console.log('✓ HTML received, inserting comment');
                    $('#comments-list').prepend(response.html);
                    form[0].reset();
                    
                    // Show success message
                    showMessage(response.message || 'Comment posted!', 'success');
                } else {
                    console.log('⚠ No HTML in response, reloading');
                    location.reload();
                }
            } else {
                console.log('✗ Response success flag is false');
                showMessage(response.error || 'Failed to post comment', 'error');
            }
            
            submitBtn.prop('disabled', false).text('Post Comment');
        },
        error: function(xhr, status, error) {
            console.log('=== ERROR RESPONSE ===');
            console.log('Status:', status);
            console.log('Error:', error);
            console.log('XHR Status:', xhr.status);
            console.log('XHR Response:', xhr.responseText);
            
            try {
                const response = JSON.parse(xhr.responseText);
                console.log('Parsed error response:', response);
                showMessage(response.error || 'Failed to save your comment. Please try again.', 'error');
            } catch(e) {
                console.log('Could not parse error response');
                showMessage('Failed to save your comment. Please try again.', 'error');
            }
            
            submitBtn.prop('disabled', false).text('Post Comment');
        },
        complete: function() {
            console.log('=== REQUEST COMPLETE ===');
        }
    });
});

// Helper function to show messages
function showMessage(message, type) {
    console.log(`showMessage called: ${type} - ${message}`);
    
    // Create message element
    const messageDiv = $('<div>')
        .addClass(`alert alert-${type === 'success' ? 'success' : 'danger'}`)
        .text(message)
        .css({
            position: 'fixed',
            top: '20px',
            right: '20px',
            zIndex: 9999,
            padding: '15px',
            borderRadius: '5px'
        });
    
    $('body').append(messageDiv);
    
    // Auto remove after 5 seconds
    setTimeout(() => messageDiv.fadeOut(() => messageDiv.remove()), 5000);
}

// IMPORTANT: Check your existing JavaScript
console.log('=== CHECKING EXISTING HANDLERS ===');
console.log('Number of submit handlers on #comment-form:', 
    $._data($('#comment-form')[0], 'events')?.submit?.length || 0);

// If you see multiple handlers, one might be interfering
// You might need to remove old handlers:
// $('#comment-form').off('submit');
