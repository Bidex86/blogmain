# comments/signals.py - Fixed to never block comment creation
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Comment
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Comment)
def calculate_comment_depth(sender, instance, **kwargs):
    """Calculate depth before saving - this should never fail"""
    try:
        if instance.parent:
            instance.depth = instance.parent.depth + 1
        else:
            instance.depth = 0
    except Exception as e:
        logger.error(f"Error calculating depth: {e}")
        instance.depth = 0  # Fallback to root level


@receiver(post_save, sender=Comment)
def comment_posted(sender, instance, created, **kwargs):
    """
    Handle actions when a comment is posted.
    IMPORTANT: This runs in a separate thread and should NEVER raise exceptions
    that would prevent comment creation.
    """
    if not created:
        return
    
    # Run all notification logic in try-except to prevent blocking
    try:
        # Send reply notification (if this is a reply)
        if instance.parent:
            try:
                send_reply_notification_safe(instance)
            except Exception as e:
                logger.warning(f"Failed to send reply notification: {e}")
        
        # Send author notification
        try:
            send_author_notification_safe(instance)
        except Exception as e:
            logger.warning(f"Failed to send author notification: {e}")
        
        # Invalidate cache
        try:
            from .utils import invalidate_comment_cache
            invalidate_comment_cache(instance.content_object)
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")
    
    except Exception as e:
        # Log but never raise - comment should still be created
        logger.error(f"Error in comment_posted signal: {e}")


def send_reply_notification_safe(comment):
    """Send email when someone replies to a comment - Safe version"""
    try:
        parent_comment = comment.parent
        if not parent_comment:
            return
        
        parent_user = parent_comment.user
        
        # Don't send email to yourself
        if parent_user == comment.user:
            return
        
        # Check if user has email
        if not parent_user.email:
            return
        
        # Check if user wants notifications (with safe checks)
        wants_email = False
        try:
            if hasattr(parent_user, 'profile') and parent_user.profile:
                wants_email = getattr(parent_user.profile, 'email_on_reply', False)
        except Exception:
            # If profile check fails, skip notification
            return
        
        if not wants_email:
            return
        
        # Send email
        subject = f'New reply to your comment'
        
        try:
            # Try to use template
            context = {
                'parent_user': parent_user,
                'reply_user': comment.user,
                'comment': comment,
                'parent_comment': parent_comment,
                'object': comment.content_object,
            }
            message = render_to_string('comments/emails/reply_notification.html', context)
        except Exception:
            # Fallback to plain text
            message = f"""
Hello {parent_user.get_full_name() or parent_user.username},

{comment.user.username} replied to your comment:

"{comment.comment}"

View the conversation at: {getattr(comment.content_object, 'get_absolute_url', lambda: '')()}

---
This is an automated message. You can change your notification preferences in your profile settings.
            """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            recipient_list=[parent_user.email],
            fail_silently=True,  # Never raise exceptions
        )
    
    except Exception as e:
        logger.error(f"Error in send_reply_notification_safe: {e}")


def send_author_notification_safe(comment):
    """Send email to content author when new comment is posted - Safe version"""
    try:
        content_object = comment.content_object
        
        # Check if content object has an author
        if not hasattr(content_object, 'author'):
            return
        
        author = content_object.author
        
        # Don't send email to yourself
        if author == comment.user:
            return
        
        # Check if author has email
        if not author.email:
            return
        
        # Check if author wants notifications (with safe checks)
        wants_email = False
        try:
            if hasattr(author, 'profile') and author.profile:
                wants_email = getattr(author.profile, 'email_on_comment', False)
        except Exception:
            # If profile check fails, skip notification
            return
        
        if not wants_email:
            return
        
        # Send email
        subject = f'New comment on your post'
        
        try:
            # Try to use template
            context = {
                'author': author,
                'comment_user': comment.user,
                'comment': comment,
                'object': content_object,
            }
            message = render_to_string('comments/emails/author_notification.html', context)
        except Exception:
            # Fallback to plain text
            message = f"""
Hello {author.get_full_name() or author.username},

{comment.user.username} commented on your post:

"{comment.comment}"

View the comment at: {getattr(content_object, 'get_absolute_url', lambda: '')()}

---
This is an automated message. You can change your notification preferences in your profile settings.
            """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            recipient_list=[author.email],
            fail_silently=True,  # Never raise exceptions
        )
    
    except Exception as e:
        logger.error(f"Error in send_author_notification_safe: {e}")