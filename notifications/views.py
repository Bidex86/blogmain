from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import PushSubscription, NotificationPreference, Notification
from .forms import NotificationPreferenceForm
from pywebpush import webpush, WebPushException
from django.conf import settings
from py_vapid import Vapid
import json
import os

@login_required
@require_http_methods(["POST"])
def subscribe(request):
    try:
        subscription_info = json.loads(request.body)
        
        PushSubscription.objects.update_or_create(
            user=request.user,
            subscription_info=subscription_info,
            defaults={'is_active': True}
        )
        
        # Create default notification preferences if they don't exist
        NotificationPreference.objects.get_or_create(user=request.user)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
def unsubscribe(request):
    try:
        subscription_info = json.loads(request.body)
        
        PushSubscription.objects.filter(
            user=request.user,
            subscription_info=subscription_info
        ).update(is_active=False)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def notification_list(request):
    """API endpoint to get user's notifications"""
    notifications = Notification.objects.filter(user=request.user)[:20]
    
    data = {
        'notifications': [
            {
                'id': n.id,
                'type': n.type,
                'title': n.title,
                'message': n.message,
                'url': n.blog_post.get_absolute_url() if n.blog_post else n.url,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat(),
            }
            for n in notifications
        ]
    }
    
    return JsonResponse(data)

@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})

@login_required
@require_http_methods(["POST"])
def mark_all_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})

@login_required
def notification_preferences(request):
    """View for managing notification preferences"""
    preference, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = NotificationPreferenceForm(request.POST, instance=preference)
        if form.is_valid():
            form.save()
            return redirect('notification_preferences')
    else:
        form = NotificationPreferenceForm(instance=preference)
    
    context = {
        'form': form,
        'preference': preference,
    }
    return render(request, 'notifications/preferences.html', context)

@login_required
def notification_history(request):
    """View all notifications"""
    notifications = Notification.objects.filter(user=request.user)\
        .select_related('blog_post__category')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'notifications/history.html', context)

def create_notification(user, notif_type, title, message, url='', blog_post=None, comment=None):
    """Helper function to create a notification"""
    notification = Notification.objects.create(
        user=user,
        type=notif_type,
        title=title,
        message=message,
        url=url,
        blog_post=blog_post,
        comment=comment,
    )
    return notification

def send_push_notification(user, title, body, url='/', image=None):
    """Send push notification to user"""
    # Check user preferences
    try:
        preference = NotificationPreference.objects.get(user=user)
        if not preference.push_enabled:
            print(f"Push notifications disabled for {user.username}")
            return
    except NotificationPreference.DoesNotExist:
        pass  # Default to sending if no preference set
    
    subscriptions = PushSubscription.objects.filter(user=user, is_active=True)
    
    payload = {
        'title': title,
        'body': body,
        'url': url,
        'image': image,
        'tag': 'blog-notification'
    }
    
    # Load VAPID key from file
    #key_path = os.path.join(settings.BASE_DIR, 'private_key.pem')
    #vapid = Vapid.from_file(key_path)
    
    for subscription in subscriptions:
        try:
            webpush(
                subscription_info=subscription.subscription_info,
                data=json.dumps(payload),
                vapid_private_key=settings.WEBPUSH_SETTINGS['VAPID_PRIVATE_KEY'],
                vapid_claims={
                    "sub": f"mailto:{settings.WEBPUSH_SETTINGS['VAPID_ADMIN_EMAIL']}"
                }
            )
            print(f"✅ Notification sent to {user.username}")
        except WebPushException as e:
            print(f"❌ Push notification failed for {user.username}: {e}")

            # A 404/410 means this subscription is dead — retire it.
            status = getattr(getattr(e, "response", None), "status_code", None)
            is_dead = status in (404, 410) or "410" in str(e) or "404" in str(e)

            if is_dead:
                subscription.is_active = False
                subscription.save(update_fields=["is_active"])
                print(f"   ↳ deactivated dead subscription {subscription.id}")

def notify_users_new_post(blog_post):
    """Notify users about a new blog post based on their preferences"""
    from django.contrib.auth.models import User
    from django.utils.html import strip_tags  # ADD THIS IMPORT
    
    # Get all users with notifications enabled
    users = User.objects.filter(profile__newsletter_opt_in=True)
    
    for user in users:
        try:
            preference = NotificationPreference.objects.get(user=user)
            
            # Check if user wants new post notifications
            if not preference.notify_new_posts:
                continue
            
            # Check if user wants notifications for this category
            if not preference.should_notify_for_category(blog_post.category):
                continue
            
        except NotificationPreference.DoesNotExist:
            pass  # Send to users without preferences
        
        # Clean the message - strip HTML tags
        raw_message = blog_post.short_description if blog_post.short_description else "Check out our latest blog post!"
        clean_message = strip_tags(raw_message)[:100]  # Strip HTML and limit to 100 chars
        
        # Create notification record
        notification = create_notification(
            user=user,
            notif_type='new_post',
            title=f"New Post: {blog_post.title}",
            message=clean_message,  # CHANGED: Use clean_message
            url=blog_post.get_absolute_url() if hasattr(blog_post, 'get_absolute_url') else '/',
            blog_post=blog_post,
        )
        
        # Send push notification
        #send_push_notification(
            #user=user,
            #title=f"New Post: {blog_post.title}",
            #body=clean_message,  # CHANGED: Use clean_message
            #url=notification.url,
            #image=blog_post.featured_image.url if blog_post.featured_image else None,
        #)
        
        #notification.is_sent = True
        #notification.save()

        # Send push notification — must never crash the loop or roll back the row
        try:
            send_push_notification(
                user=user,
                title=f"New Post: {blog_post.title}",
                body=clean_message,
                url=notification.url,
                image=blog_post.featured_image.url if blog_post.featured_image else None,
            )
            notification.is_sent = True
            notification.save()
        except Exception as e:
            print(f"⚠️ Push failed for {user} (in-app notification still saved): {e}")