# Add these template filters to comments/templatetags/comment_tags.py

from django import template
from django.contrib.contenttypes.models import ContentType
from comments.models import Comment
from comments.forms import CommentForm

register = template.Library()

@register.simple_tag
def comment_count_for(obj):
    """Get total comment count for any object"""
    return Comment.objects.for_object(obj).filter(is_approved=True).count()

@register.inclusion_tag('comments/comment_list.html', takes_context=True)
def get_comments_for(context, obj, paginate_by=10):
    """Get paginated comments for an object"""
    from django.core.paginator import Paginator
    
    # Fix: Use filter() instead of non-existent approved() method
    comments = Comment.objects.top_level_for_object(obj).filter(
        is_approved=True
    ).select_related(
        'user'
    ).prefetch_related(
        'children__user'
    ).order_by('-created_at')
    
    # Handle pagination
    page_number = context['request'].GET.get('page', 1)
    paginator = Paginator(comments, paginate_by)
    page_obj = paginator.get_page(page_number)
    
    return {
        'comments': page_obj,
        'object': obj,
        'user': context.get('user'),
        'request': context['request'],
        'content_type_id': ContentType.objects.get_for_model(obj).id,
    }

@register.filter
def can_reply_to(comment, user):
    """Check if user can reply to a comment"""
    if not user.is_authenticated:
        return False
    if comment.max_depth_reached:
        return False
    return True

@register.filter
def can_be_edited_by(comment, user):
    """Check if comment can be edited by user - TEMPLATE FILTER VERSION"""
    return comment.can_be_edited_by(user)

@register.filter
def depth_class(depth):
    """Get CSS class for comment depth"""
    return f"depth-{min(depth, 4)}"  # Cap at depth-4 for CSS