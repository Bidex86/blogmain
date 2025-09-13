# comments/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Comment

@receiver(post_save, sender=Comment)
def comment_posted(sender, instance, created, **kwargs):
    """Handle actions when a comment is posted"""
    if not created:
        return
    
    # Send email notification to parent comment author
    if instance.parent and instance.parent.user.profile.email_on_reply:
        send_reply_notification(instance)
    
    # Send email to content object author
    send_author_notification(instance)
    
    # Update comment count cache (if using caching)
    #update_comment_count_cache(instance.content_object)

def send_reply_notification(comment):
    """Send email when someone replies to a comment"""
    parent_comment = comment.parent
    parent_user = parent_comment.user
    
    if parent_user.email and parent_user != comment.user:
        subject = f'New reply to your comment on {comment.content_object}'
        
        context = {
            'parent_user': parent_user,
            'reply_user': comment.user,
            'comment': comment,
            'parent_comment': parent_comment,
            'object': comment.content_object,
        }
        
        message = render_to_string('comments/emails/reply_notification.html', context)
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[parent_user.email],
            fail_silently=True,
        )

def send_author_notification(comment):
    """Send email to content author when new comment is posted"""
    content_object = comment.content_object
    
    # Check if content object has an author field
    if hasattr(content_object, 'author'):
        author = content_object.author
        if (author.email and 
            author != comment.user and 
            hasattr(author, 'profile') and 
            author.profile.email_on_reply):
            
            subject = f'New comment on your post: {content_object}'
            
            context = {
                'author': author,
                'comment_user': comment.user,
                'comment': comment,
                'object': content_object,
            }
            
            message = render_to_string('comments/emails/author_notification.html', context)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[author.email],
                fail_silently=True,
            )