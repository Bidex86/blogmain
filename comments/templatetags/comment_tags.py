# comments/templatetags/comment_tags.py - Complete working version
from django import template
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator

register = template.Library()

@register.inclusion_tag('comments/comment_list.html', takes_context=True)
def render_comments(context, obj, paginate_by=10):
    """Render comments for an object"""
    try:
        from comments.models import Comment
        
        # Get top-level comments (no parent)
        comments_qs = Comment.objects.filter(
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            parent=None,
            is_approved=True
        ).select_related('user').prefetch_related(
            'likes',
            'children__user',
            'children__likes'
        ).order_by('-created_at')
        
        # Handle pagination
        page_number = context.get('request', {}).GET.get('page', 1)
        paginator = Paginator(comments_qs, paginate_by)
        page_obj = paginator.get_page(page_number)
        
    except Exception as e:
        print(f"Error in render_comments: {e}")
        page_obj = []
    
    return {
        'comments': page_obj,
        'object': obj,
        'user': context.get('user'),
        'request': context.get('request'),
        'content_type_id': ContentType.objects.get_for_model(obj).id,
    }

@register.inclusion_tag('comments/comment_list.html', takes_context=True)
def get_comments_for(context, obj, paginate_by=10):
    """Alternative name for render_comments"""
    return render_comments(context, obj, paginate_by)

@register.simple_tag
def comment_count_for(obj):
    """Get total comment count for any object"""
    try:
        from comments.models import Comment
        return Comment.objects.filter(
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            is_approved=True
        ).count()
    except:
        return 0

@register.filter
def can_reply_to(comment, user):
    """Check if user can reply to a comment"""
    if not user or not user.is_authenticated:
        return False
    try:
        # Check max depth
        if hasattr(comment, 'max_depth_reached') and comment.max_depth_reached:
            return False
        # Simple depth check as fallback
        if hasattr(comment, 'depth') and comment.depth >= 4:
            return False
    except:
        pass
    return True

@register.filter
def can_be_edited_by(comment, user):
    """Check if comment can be edited by user"""
    if not user or not user.is_authenticated:
        return False
    try:
        if hasattr(comment, 'can_be_edited_by'):
            return comment.can_be_edited_by(user)
    except:
        pass
    # Fallback logic
    if user.is_staff:
        return True
    return comment.user == user

@register.filter
def user_has_liked(comment, user):
    """Check if user has liked this comment - FIXED VERSION"""
    if not user or not user.is_authenticated:
        return False
    try:
        return comment.likes.filter(user=user).exists()
    except Exception as e:
        print(f"Error checking like status: {e}")
        return False

@register.filter
def depth_class(depth):
    """Get CSS class for comment depth"""
    try:
        return f"depth-{min(int(depth), 4)}"
    except:
        return "depth-0"

@register.filter
def get_avatar_url(user):
    """Safely get user avatar URL"""
    try:
        if hasattr(user, 'profile') and user.profile:
            if hasattr(user.profile, 'avatar') and user.profile.avatar:
                return user.profile.avatar.url
    except:
        pass
    return '/static/images/default-avatar.png'

@register.filter
def content_type_id(obj):
    """Get content type ID for any object"""
    try:
        return ContentType.objects.get_for_model(obj).id
    except:
        return None