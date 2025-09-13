document.addEventListener('DOMContentLoaded', function() {
    // Simple delete confirmation for all delete links
    document.querySelectorAll('a[href*="delete"]').forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            let itemName = this.getAttribute('data-item-name') || 'this item';
            let itemType = this.getAttribute('data-item-type') || 'item';
            
            if (confirm(`Are you sure you want to delete ${itemType}: "${itemName}"?`)) {
                // Add a flag to force refresh after delete
                sessionStorage.setItem('just_deleted', 'true');
                window.location.href = this.href;
            }
        });
    });
    
    // Check if we just deleted something and show message
    if (sessionStorage.getItem('just_deleted')) {
        sessionStorage.removeItem('just_deleted');
        // Force page refresh to show updated data
        if (performance.navigation.type !== performance.navigation.TYPE_RELOAD) {
            location.reload(true);
        }
    }
});

// Force refresh when using browser back button
window.addEventListener('pageshow', function(event) {
    if (event.persisted) {
        location.reload(true);
    }
});