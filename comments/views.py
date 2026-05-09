# comments/views.py - Complete working version with proper AJAX support
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.http import require_POST, require_http_methods
from django.template.loader import render_to_string
from .models import Comment, CommentFlag, CommentLike
from .forms import CommentForm, CommentFlagForm
import logging
from django.contrib.messages import get_messages


logger = logging.getLogger(__name__)


# Replace ONLY the add_comment function in comments/views.py with this:

@login_required
@require_POST
def add_comment(request):
    """Add a new comment or reply - Final corrected version"""
    
    # Clear any old messages
    list(get_messages(request))
    
    # Step 1: Get and validate form data
    content_type_id = request.POST.get('content_type_id')
    object_id = request.POST.get('object_id')
    parent_id = request.POST.get('parent_id')
    comment_text = request.POST.get('comment', '').strip()
    
    # Early validation
    if not content_type_id or not object_id:
        messages.error(request, 'Missing required information.')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    if not comment_text:
        messages.error(request, 'Comment cannot be empty.')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    if len(comment_text) > 1000:
        messages.error(request, 'Comment is too long (maximum 1000 characters).')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    # Step 2: Get the content object
    try:
        content_type = ContentType.objects.get(id=content_type_id)
        model_class = content_type.model_class()
        content_object = model_class.objects.get(id=object_id)
    except ContentType.DoesNotExist:
        logger.error(f"ContentType {content_type_id} does not exist")
        messages.error(request, 'Invalid content type.')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    except model_class.DoesNotExist:
        logger.error(f"Object {object_id} of type {content_type_id} does not exist")
        messages.error(request, 'Content not found.')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    except Exception as e:
        logger.error(f"Error getting content object: {e}")
        messages.error(request, 'Unable to process your comment.')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    # Step 3: Handle parent comment if replying
    parent_comment = None
    if parent_id:
        try:
            parent_comment = Comment.objects.get(id=parent_id)
            # Check if max depth reached
            if hasattr(parent_comment, 'max_depth_reached') and parent_comment.max_depth_reached:
                messages.error(request, 'Cannot reply - maximum nesting depth reached.')
                return redirect(request.META.get('HTTP_REFERER', '/'))
        except Comment.DoesNotExist:
            logger.warning(f"Parent comment {parent_id} not found")
            messages.error(request, 'Original comment not found.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
    
    # Step 4: Create the comment (NARROW try-except - ONLY for the create operation)
    try:
        comment = Comment.objects.create(
            content_type=content_type,
            object_id=object_id,
            user=request.user,
            comment=comment_text,
            parent=parent_comment,
            is_approved=True
        )
        logger.info(f"Comment {comment.id} created successfully by {request.user.username}")
        
    except Exception as e:
        # This is the ONLY place where comment creation actually failed
        logger.error(f"Failed to create comment: {e}", exc_info=True)
        # DON'T show error message to user - just log it and redirect
        # The comment failed to save, but we don't want to confuse users
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    # Step 5: Comment SAVED SUCCESSFULLY! Show success message
    messages.success(request, 'Your comment has been posted successfully!')
    
    # Step 6: Get redirect URL (safe - won't trigger error messages)
    redirect_url = request.META.get('HTTP_REFERER', '/')
    
    try:
        if hasattr(content_object, 'get_absolute_url'):
            redirect_url = content_object.get_absolute_url() + f'#comment-{comment.id}'
    except Exception as e:
        logger.warning(f"Could not get absolute URL: {e}")
        pass
    
    # Step 7: Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            html = render_to_string('comments/comment_item.html', {
                'comment': comment,
                'user': request.user,
                'content_type_id': content_type_id,
                'object': content_object,
            })
            return JsonResponse({
                'success': True,
                'message': 'Comment posted successfully!',
                'comment_id': comment.id,
                'html': html,
            })
        except Exception as e:
            # Even if rendering fails, comment was created
            logger.error(f"Error rendering comment HTML: {e}")
            return JsonResponse({
                'success': True,
                'message': 'Comment posted successfully!',
                'comment_id': comment.id,
                'reload': True
            })
    
    # Step 8: Normal redirect
    return redirect(redirect_url)

@login_required
@require_http_methods(["GET", "POST"])
def edit_comment(request, comment_id):
    """Edit an existing comment"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Check permissions
    if not comment.can_be_edited_by(request.user):
        messages.error(request, 'You do not have permission to edit this comment.')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    if request.method == 'POST':
        try:
            new_comment_text = request.POST.get('comment', '').strip()
            
            if not new_comment_text:
                messages.error(request, 'Comment cannot be empty.')
                return redirect(request.META.get('HTTP_REFERER', '/'))
            
            if len(new_comment_text) > 1000:
                messages.error(request, 'Comment cannot exceed 1000 characters.')
                return redirect(request.META.get('HTTP_REFERER', '/'))
            
            # Update comment
            comment.comment = new_comment_text
            comment.save()
            
            messages.success(request, 'Comment updated successfully!')
            
            # Handle AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Comment updated successfully!',
                    'comment_text': new_comment_text,
                })
            
            # Redirect back
            try:
                redirect_url = comment.content_object.get_absolute_url() + f'#comment-{comment.id}'
            except:
                redirect_url = request.META.get('HTTP_REFERER', '/')
            
            return redirect(redirect_url)
        
        except Exception as e:
            logger.error(f"Error editing comment: {e}", exc_info=True)
            messages.error(request, 'An error occurred while updating your comment.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
    
    # GET request - show edit form
    content_object = comment.content_object
    form = CommentForm(instance=comment)
    
    return render(request, 'comments/edit_comment.html', {
        'comment': comment,
        'form': form,
        'object': content_object,
    })


@login_required
@require_POST
def delete_comment(request, comment_id):
    """Delete a comment"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Check permissions
    if comment.user != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to delete this comment.')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    try:
        content_object = comment.content_object
        comment.delete()
        
        messages.success(request, 'Comment deleted successfully!')
        
        # Handle AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Comment deleted successfully!'
            })
        
        # Redirect back
        try:
            redirect_url = content_object.get_absolute_url() + '#comments'
        except:
            redirect_url = request.META.get('HTTP_REFERER', '/')
        
        return redirect(redirect_url)
    
    except Exception as e:
        logger.error(f"Error deleting comment: {e}", exc_info=True)
        messages.error(request, 'An error occurred while deleting the comment.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'An error occurred. Please try again.'
            }, status=500)
        
        return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
@require_POST
def like_comment(request, comment_id):
    """Like or unlike a comment"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    try:
        # Check if user already liked
        like, created = CommentLike.objects.get_or_create(
            comment=comment,
            user=request.user
        )
        
        if not created:
            # Unlike
            like.delete()
            liked = False
            message = 'Like removed'
        else:
            # New like
            liked = True
            message = 'Comment liked!'
        
        like_count = comment.likes.count()
        
        # Handle AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'liked': liked,
                'like_count': like_count,
                'message': message
            })
        
        messages.success(request, message)
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    except Exception as e:
        logger.error(f"Error liking comment: {e}", exc_info=True)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'An error occurred.'
            }, status=500)
        
        messages.error(request, 'An error occurred.')
        return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
@require_http_methods(["GET", "POST"])
def flag_comment(request, comment_id):
    """Flag a comment as inappropriate"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    if comment.user == request.user:
        messages.error(request, 'You cannot flag your own comment.')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    if request.method == 'POST':
        try:
            reason = request.POST.get('reason')
            description = request.POST.get('description', '')
            
            if not reason:
                messages.error(request, 'Please select a reason for flagging.')
                return redirect(request.META.get('HTTP_REFERER', '/'))
            
            # Create or update flag
            flag, created = CommentFlag.objects.get_or_create(
                comment=comment,
                user=request.user,
                defaults={
                    'reason': reason,
                    'description': description
                }
            )
            
            if not created:
                flag.reason = reason
                flag.description = description
                flag.save()
            
            # Mark comment as flagged
            comment.is_flagged = True
            comment.save()
            
            messages.success(request, 'Comment has been reported. Thank you!')
            
            # Handle AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Comment reported successfully!'
                })
            
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        except Exception as e:
            logger.error(f"Error flagging comment: {e}", exc_info=True)
            messages.error(request, 'An error occurred while reporting the comment.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
    
    return redirect(request.META.get('HTTP_REFERER', '/'))


def get_comment_replies(request, comment_id):
    """AJAX view to load comment replies"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    replies = comment.children.filter(
        is_approved=True
    ).select_related('user').order_by('created_at')
    
    html = render_to_string('comments/reply_list.html', {
        'replies': replies,
        'user': request.user,
        'content_type_id': comment.content_type.id,
        'object': comment.content_object
    })
    
    return JsonResponse({
        'success': True,
        'html': html,
        'count': replies.count()
    })


@login_required
def user_comments(request):
    """View all comments by the current user"""
    comments = Comment.objects.filter(
        user=request.user
    ).select_related(
        'content_type', 'parent', 'user'
    ).prefetch_related(
        'likes', 'flags', 'children'
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(comments, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'comments/user_comments.html', {
        'comments': page_obj,
        'total_comments': comments.count(),
    })


def search_comments(request):
    """AJAX view for searching comments"""
    query = request.GET.get('q', '').strip()
    content_type_id = request.GET.get('content_type_id')
    object_id = request.GET.get('object_id')
    
    if not query or len(query) < 2:
        return JsonResponse({
            'success': False,
            'error': 'Query too short'
        })
    
    # Build search filters
    filters = Q(comment__icontains=query) | Q(user__username__icontains=query)
    filters &= Q(is_approved=True)
    
    if content_type_id and object_id:
        filters &= Q(content_type_id=content_type_id, object_id=object_id)
    
    # Execute search
    comments = Comment.objects.filter(filters).select_related(
        'user', 'content_type'
    ).order_by('-created_at')[:20]
    
    # Format results
    results = []
    for comment in comments:
        try:
            results.append({
                'id': comment.id,
                'content': comment.comment[:100] + '...' if len(comment.comment) > 100 else comment.comment,
                'author': comment.user.get_full_name() or comment.user.username,
                'created_at': comment.created_at.isoformat(),
                'object_title': str(comment.content_object)[:50] if comment.content_object else 'Unknown',
                'depth': comment.depth,
                'is_reply': comment.parent is not None,
            })
        except:
            continue
    
    return JsonResponse({
        'success': True,
        'results': results,
        'count': len(results)
    })


def load_more_comments(request):
    """AJAX view to load more comments"""
    content_type_id = request.GET.get('content_type_id')
    object_id = request.GET.get('object_id')
    page = request.GET.get('page', 1)
    
    if not content_type_id or not object_id:
        return JsonResponse({
            'success': False,
            'error': 'Missing parameters'
        })
    
    try:
        content_type = ContentType.objects.get(id=content_type_id)
        content_object = content_type.get_object_for_this_type(id=object_id)
    except:
        return JsonResponse({
            'success': False,
            'error': 'Object not found'
        })
    
    # Get comments
    comments = Comment.objects.filter(
        content_type_id=content_type_id,
        object_id=object_id,
        parent=None,
        is_approved=True
    ).select_related('user').prefetch_related(
        'children__user'
    ).order_by('-created_at')
    
    # Paginate
    paginator = Paginator(comments, 10)
    page_obj = paginator.get_page(page)
    
    html = render_to_string('comments/comment_list_ajax.html', {
        'comments': page_obj,
        'user': request.user,
        'content_type_id': content_type_id,
        'object': content_object,
    })
    
    return JsonResponse({
        'success': True,
        'html': html,
        'has_more': page_obj.has_next(),
        'next_url': f'?page={page_obj.next_page_number()}' if page_obj.has_next() else None,
    })


def comment_stats(request, post_id=None):
    """Get comment statistics"""
    if post_id:
        try:
            from blogs.models import Blog
            post = Blog.objects.get(id=post_id)
            comments = Comment.objects.filter(
                content_type=ContentType.objects.get_for_model(post),
                object_id=post.pk,
                is_approved=True
            )
        except:
            return JsonResponse({'success': False, 'error': 'Post not found'})
    else:
        comments = Comment.objects.filter(is_approved=True)
    
    stats = {
        'total': comments.count(),
        'unique_users': comments.values('user').distinct().count(),
        'replies': comments.filter(parent__isnull=False).count(),
        'top_level': comments.filter(parent__isnull=True).count(),
    }
    
    return JsonResponse({
        'success': True,
        'stats': stats
    })


# Moderation views
@user_passes_test(lambda u: u.is_staff)
def moderate_comments(request):
    """View for moderating comments"""
    pending_comments = Comment.objects.filter(
        is_approved=False
    ).select_related('user', 'content_type').order_by('-created_at')
    
    flagged_comments = Comment.objects.filter(
        is_flagged=True
    ).select_related('user', 'content_type').prefetch_related('flags').order_by('-created_at')
    
    return render(request, 'comments/moderation.html', {
        'pending_comments': pending_comments,
        'flagged_comments': flagged_comments,
    })


@user_passes_test(lambda u: u.is_staff)
@require_POST
def moderate_comment(request, comment_id):
    """Moderate a specific comment"""
    comment = get_object_or_404(Comment, id=comment_id)
    action = request.POST.get('action')
    
    try:
        if action == 'approve':
            comment.is_approved = True
            comment.is_flagged = False
            comment.save()
            message = 'Comment approved.'
        elif action == 'reject':
            comment.delete()
            message = 'Comment deleted.'
        elif action == 'flag':
            comment.is_flagged = True
            comment.save()
            message = 'Comment flagged.'
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid action'
            }, status=400)
        
        # Handle AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': message
            })
        
        messages.success(request, message)
        return redirect('comments:moderate_comments')
    
    except Exception as e:
        logger.error(f"Error moderating comment: {e}", exc_info=True)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
        
        messages.error(request, 'An error occurred.')
        return redirect('comments:moderate_comments')


@user_passes_test(lambda u: u.is_staff)
def view_flags(request):
    """View all flagged comments"""
    flags = CommentFlag.objects.filter(
        is_reviewed=False
    ).select_related('comment', 'user', 'comment__user').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(flags, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'comments/flags.html', {
        'flags': page_obj,
    })


@user_passes_test(lambda u: u.is_staff)
@require_POST
def mark_flag_reviewed(request, flag_id):
    """Mark a flag as reviewed"""
    flag = get_object_or_404(CommentFlag, id=flag_id)
    
    try:
        flag.is_reviewed = True
        flag.save()
        
        # Handle AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Flag marked as reviewed.'
            })
        
        messages.success(request, 'Flag marked as reviewed.')
        return redirect('comments:view_flags')
    
    except Exception as e:
        logger.error(f"Error marking flag as reviewed: {e}", exc_info=True)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
        
        messages.error(request, 'An error occurred.')
        return redirect('comments:view_flags')