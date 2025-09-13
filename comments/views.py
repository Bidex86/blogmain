# comments/views.py - Complete implementation
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.db.models import Q
from django.conf import settings
from .models import Comment, CommentFlag, CommentLike
from .forms import CommentForm


@login_required
@require_POST
def add_comment(request):
    """
    Generic view to add comments to any model
    Expects: content_type_id, object_id, comment, parent_id (optional)
    """
    # Get the object being commented on
    content_type_id = request.POST.get('content_type_id')
    object_id = request.POST.get('object_id')
    
    if not content_type_id or not object_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Missing object information'})
        messages.error(request, 'Invalid request.')
        return redirect('home')
    
    try:
        content_type = ContentType.objects.get(id=content_type_id)
        content_object = content_type.get_object_for_this_type(id=object_id)
    except (ContentType.DoesNotExist, content_type.model_class().DoesNotExist):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Object not found'})
        messages.error(request, 'Object not found.')
        return redirect('home')
    
    # Create the comment
    form = CommentForm(request.POST, content_object=content_object, user=request.user)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.content_object = content_object
        comment.user = request.user
        
        # Handle parent comment for replies
        parent_id = request.POST.get('parent_id')
        if parent_id:
            try:
                parent_comment = Comment.objects.get(
                    id=parent_id,
                    content_type=content_type,
                    object_id=object_id
                )
                # Check depth limit
                max_depth = getattr(settings, 'COMMENTS_MAX_DEPTH', 4)
                if parent_comment.depth >= max_depth - 1:
                    raise ValidationError('Maximum reply depth reached')
                
                comment.parent = parent_comment
                success_message = f'Reply to {parent_comment.user.username} posted!'
            except Comment.DoesNotExist:
                messages.error(request, 'Parent comment not found.')
                return redirect_to_object(content_object)
            except ValidationError as e:
                messages.error(request, str(e))
                return redirect_to_object(content_object)
        else:
            success_message = 'Comment posted successfully!'
        
        comment.save()
        
        # Handle AJAX response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': success_message,
                'comment_html': render_comment_to_html(comment, request.user),
                'comment_id': comment.id
            })
        
        messages.success(request, success_message)
    else:
        # Handle form errors
        error_messages = []
        for field, errors in form.errors.items():
            error_messages.extend(errors)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': error_messages
            })
        
        for error in error_messages:
            messages.error(request, error)
    
    # Redirect back to the object
    return redirect_to_object(content_object)


@login_required
def edit_comment(request, comment_id):
    """Edit a comment"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    if not comment.can_be_edited_by(request.user):
        messages.error(request, "You cannot edit this comment.")
        return redirect_to_object(comment.content_object)
    
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment, content_object=comment.content_object, user=request.user)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.is_edited = True
            comment.save()
            messages.success(request, "Comment updated successfully.")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Comment updated successfully.',
                    'comment_html': render_comment_to_html(comment, request.user)
                })
            
            return redirect_to_object(comment.content_object)
    else:
        # Pre-populate form with existing comment data
        initial_data = {
            'comment': comment.comment,
            'content_type_id': comment.content_type.id,
            'object_id': comment.object_id,
        }
        if comment.parent:
            initial_data['parent_id'] = comment.parent.id
            
        form = CommentForm(initial=initial_data, instance=comment, content_object=comment.content_object, user=request.user)
    
    return render(request, 'comments/edit_comment.html', {
        'form': form,
        'comment': comment,
        'object': comment.content_object
    })


@login_required
@require_POST
def delete_comment(request, comment_id):
    """Delete a comment"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    if comment.user != request.user and not request.user.is_staff:
        messages.error(request, "You cannot delete this comment.")
        return redirect_to_object(comment.content_object)
    
    content_object = comment.content_object
    comment.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Comment deleted successfully.'
        })
    
    messages.success(request, "Comment deleted successfully.")
    return redirect_to_object(content_object)


@login_required
@require_POST
def flag_comment(request, comment_id):
    """Flag a comment as inappropriate"""
    comment = get_object_or_404(Comment, id=comment_id)
    reason = request.POST.get('reason', 'inappropriate')
    description = request.POST.get('description', '')
    
    flag, created = CommentFlag.objects.get_or_create(
        comment=comment,
        user=request.user,
        defaults={
            'reason': reason,
            'description': description
        }
    )
    
    if created:
        # Mark comment as flagged if it receives multiple flags
        flag_count = comment.flags.count()
        if flag_count >= 3:  # Threshold for auto-flagging
            comment.is_flagged = True
            comment.save()
        
        message = "Comment flagged for review."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': message})
        messages.success(request, message)
    else:
        message = "You have already flagged this comment."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': message})
        messages.info(request, message)
    
    return redirect_to_object(comment.content_object)


@login_required
@require_POST
def like_comment(request, comment_id):
    """Like/unlike a comment"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    like, created = CommentLike.objects.get_or_create(
        comment=comment,
        user=request.user
    )
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    
    like_count = comment.likes.count()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'liked': liked,
            'like_count': like_count
        })
    
    return redirect_to_object(comment.content_object)


def get_comment_replies(request, comment_id):
    """AJAX view to load comment replies"""
    comment = get_object_or_404(Comment, id=comment_id)
    replies = comment.children.approved().select_related('user').order_by('created_at')
    
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


def search_comments(request):
    """AJAX view for searching comments"""
    query = request.GET.get('q', '').strip()
    content_type_id = request.GET.get('content_type_id')
    object_id = request.GET.get('object_id')
    
    if not query or len(query) < 2:
        return JsonResponse({'success': False, 'error': 'Query too short'})
    
    # Build search filters
    filters = Q(comment__icontains=query) | Q(user__username__icontains=query)
    
    if content_type_id and object_id:
        filters &= Q(content_type_id=content_type_id, object_id=object_id)
    
    # Execute search
    comments = Comment.objects.filter(filters).approved().select_related(
        'user', 'content_type'
    ).order_by('-created_at')[:20]
    
    # Format results
    results = []
    for comment in comments:
        results.append({
            'id': comment.id,
            'content': comment.comment[:100] + '...' if len(comment.comment) > 100 else comment.comment,
            'author': comment.user.get_full_name() or comment.user.username,
            'created_at': comment.created_at.isoformat(),
            'object_title': str(comment.content_object),
            'depth': comment.depth,
            'is_reply': comment.parent is not None,
        })
    
    return JsonResponse({
        'success': True,
        'results': results,
        'count': len(results)
    })


def redirect_to_object(obj):
    """Helper to redirect back to the commented object"""
    if hasattr(obj, 'get_absolute_url'):
        return redirect(f"{obj.get_absolute_url()}#comments")
    else:
        # Fallback - customize this for your needs
        return redirect('home')


def render_comment_to_html(comment, user=None):
    """Render a single comment to HTML for AJAX responses"""
    return render_to_string('comments/comment_item.html', {
        'comment': comment,
        'user': user,
        'content_type_id': comment.content_type.id,
        'object': comment.content_object,
    })


# Additional utility views for moderation (optional)
@login_required
def moderate_comments(request):
    """View for comment moderation (staff only)"""
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('home')
    
    pending_comments = Comment.objects.filter(is_approved=False).select_related('user', 'content_type')
    flagged_comments = Comment.objects.filter(is_flagged=True).select_related('user', 'content_type')
    
    return render(request, 'comments/moderation.html', {
        'pending_comments': pending_comments,
        'flagged_comments': flagged_comments,
    })


@login_required
@require_POST
def moderate_comment(request, comment_id):
    """Approve or reject a comment (staff only)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    comment = get_object_or_404(Comment, id=comment_id)
    action = request.POST.get('action')
    
    if action == 'approve':
        comment.is_approved = True
        comment.is_flagged = False
        comment.save()
        message = 'Comment approved.'
    elif action == 'reject':
        comment.delete()
        message = 'Comment deleted.'
    else:
        return JsonResponse({'success': False, 'error': 'Invalid action'})
    
    return JsonResponse({'success': True, 'message': message})


def view_flags(request):
    """View flagged comments (staff only)"""
    if not request.user.is_staff:
        messages.error(request, "Permission denied.")
        return redirect('home')
    
    flags = CommentFlag.objects.filter(is_reviewed=False).select_related(
        'comment', 'comment__user', 'user'
    ).order_by('-created_at')
    
    return render(request, 'comments/flags.html', {
        'flags': flags,
    })

# Additional views to add to comments/views.py

@login_required
@require_POST
def mark_flag_reviewed(request, flag_id):
    """Mark a flag as reviewed (staff only)"""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    flag = get_object_or_404(CommentFlag, id=flag_id)
    flag.is_reviewed = True
    flag.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Flag marked as reviewed.'
    })


def comment_stats(request, post_id=None):
    """Get comment statistics for a post"""
    if post_id:
        from blogs.models import Blog
        post = get_object_or_404(Blog, id=post_id)
        comments = Comment.objects.for_object(post)
    else:
        comments = Comment.objects.all()
    
    stats = {
        'total_comments': comments.count(),
        'approved_comments': comments.filter(is_approved=True).count(),
        'pending_comments': comments.filter(is_approved=False).count(),
        'flagged_comments': comments.filter(is_flagged=True).count(),
        'unique_commenters': comments.values('user').distinct().count(),
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(stats)
    
    return render(request, 'comments/stats.html', {'stats': stats})


@login_required
def user_comments(request):
    """View user's own comments"""
    user_comments = Comment.objects.filter(user=request.user).select_related(
        'content_type'
    ).order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(user_comments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'comments/user_comments.html', {
        'comments': page_obj,
        'total_comments': user_comments.count(),
    })


def load_more_comments(request):
    """AJAX view to load more comments with pagination"""
    content_type_id = request.GET.get('content_type_id')
    object_id = request.GET.get('object_id')
    page = request.GET.get('page', 1)
    
    if not content_type_id or not object_id:
        return JsonResponse({'success': False, 'error': 'Missing parameters'})
    
    try:
        content_type = ContentType.objects.get(id=content_type_id)
        content_object = content_type.get_object_for_this_type(id=object_id)
    except (ContentType.DoesNotExist, content_type.model_class().DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Object not found'})
    
    comments = Comment.objects.top_level_for_object(content_object).approved().select_related(
        'user'
    ).prefetch_related(
        'children__user'
    ).order_by('-created_at')
    
    from django.core.paginator import Paginator
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