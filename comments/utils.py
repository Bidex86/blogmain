# comments/utils.py
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.template.loader import render_to_string
from .models import Comment
import hashlib

def get_comment_tree(obj, max_depth=None):
    """
    Get a hierarchical tree of comments for an object
    Returns nested dictionary structure
    """
    comments = Comment.objects.for_object(obj).approved().select_related('user')
    
    # Build tree structure
    comment_dict = {}
    root_comments = []
    
    # First pass: create lookup dictionary
    for comment in comments:
        comment.children_list = []
        comment_dict[comment.id] = comment
    
    # Second pass: build tree
    for comment in comments:
        if comment.parent_id:
            if comment.parent_id in comment_dict:
                parent = comment_dict[comment.parent_id]
                if max_depth is None or parent.depth < max_depth:
                    parent.children_list.append(comment)
        else:
            root_comments.append(comment)
    
    return root_comments

def render_comment_html(comment, user=None):
    """Render a single comment to HTML"""
    return render_to_string('comments/comment_thread.html', {
        'comment': comment,
        'depth': comment.depth,
        'user': user,
    })

def get_comment_cache_key(obj):
    """Generate cache key for comment data"""
    content_type = ContentType.objects.get_for_model(obj)
    return f"comments:{content_type.id}:{obj.id}"

def invalidate_comment_cache(obj):
    """Invalidate cached comment data when comments change"""
    cache_key = get_comment_cache_key(obj)
    cache.delete(cache_key)

def detect_spam_content(text):
    """Basic spam detection for comments"""
    spam_indicators = [
        # URL patterns
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+])+',
        # Repeated characters
        r'(.)\1{5,}',
        # Common spam phrases
        r'\b(viagra|casino|lottery|winner|prize|congratulations|click here)\b',
        # Excessive punctuation
        r'[!]{3,}',
    ]
    
    import re
    spam_score = 0
    
    for pattern in spam_indicators:
        if re.search(pattern, text, re.IGNORECASE):
            spam_score += 1
    
    return spam_score >= 2  # Threshold for spam

def sanitize_comment(text):
    """Clean and sanitize comment text"""
    from django.utils.html import strip_tags
    import html
    
    # Remove HTML tags
    text = strip_tags(text)
    
    # Escape HTML entities
    text = html.escape(text)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text.strip()