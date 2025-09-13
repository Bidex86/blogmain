# dashboard/email_utils.py
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from accounts.models import Profile
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

def send_newsletter_email(post):
    """
    Send newsletter email to all subscribed users when a new post is published
    """
    try:
        # Get all users who are subscribed to the newsletter
        subscribed_profiles = Profile.objects.filter(newsletter_opt_in=True).select_related('user')
        
        if not subscribed_profiles.exists():
            logger.info("No subscribers found for newsletter")
            return
        
        # Prepare email content
        subject = f"New Post: {post.title}"
        
        # Create the context for email template
        context = {
            'post': post,
            'site_name': getattr(settings, 'SITE_NAME', 'Our Blog'),
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        # Render HTML and text versions
        html_content = render_to_string('emails/newsletter_post.html', context)
        text_content = render_to_string('emails/newsletter_post.txt', context)
        
        # Get subscriber emails
        subscriber_emails = [profile.user.email for profile in subscribed_profiles if profile.user.email]
        
        if not subscriber_emails:
            logger.info("No valid email addresses found for subscribers")
            return
        
        # Send emails in batches to avoid overwhelming the email server
        batch_size = 50  # Adjust based on your email provider limits
        for i in range(0, len(subscriber_emails), batch_size):
            batch_emails = subscriber_emails[i:i + batch_size]
            
            try:
                # Create email message
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    bcc=batch_emails,  # Use BCC to hide recipient addresses
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                
                logger.info(f"Newsletter sent to {len(batch_emails)} subscribers")
                
            except Exception as e:
                logger.error(f"Failed to send newsletter to batch: {e}")
                continue
        
        logger.info(f"Newsletter campaign completed. Total emails sent to {len(subscriber_emails)} subscribers")
        
    except Exception as e:
        logger.error(f"Failed to send newsletter: {e}")


def send_individual_notification(user_email, post):
    """
    Send notification to a specific user (useful for testing)
    """
    try:
        subject = f"New Post: {post.title}"
        
        context = {
            'post': post,
            'site_name': getattr(settings, 'SITE_NAME', 'Our Blog'),
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }
        
        html_content = render_to_string('emails/newsletter_post.html', context)
        text_content = render_to_string('emails/newsletter_post.txt', context)
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        logger.info(f"Individual notification sent to {user_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send individual notification: {e}")
        return False