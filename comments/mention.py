# comments/mentions.py
import re
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings

class CommentMentionProcessor:
    """Handle @username mentions in comments"""
    
    @staticmethod
    def extract_mentions(comment_text):
        """Extract @username mentions from comment text"""
        mention_pattern = r'@(\w+)'
        mentions = re.findall(mention_pattern, comment_text)
        return list(set(mentions))  # Remove duplicates
    
    @staticmethod
    def process_mentions(comment):
        """Process mentions in a comment and send notifications"""
        mentions = CommentMentionProcessor.extract_mentions(comment.comment)
        
        for username in mentions:
            try:
                mentioned_user = User.objects.get(username=username)
                if (mentioned_user != comment.user and 
                    hasattr(mentioned_user, 'profile') and
                    mentioned_user.profile.email_on_mention):
                    
                    CommentMentionProcessor.send_mention_notification(
                        comment, mentioned_user
                    )
            except User.DoesNotExist:
                continue
    
    @staticmethod
    def send_mention_notification(comment, mentioned_user):
        """Send email notification for mentions"""
        subject = f'You were mentioned in a comment by {comment.user.username}'
        
        context = {
            'mentioned_user': mentioned_user,
            'comment_user': comment.user,
            'comment': comment,
            'object': comment.content_object,
        }
        
        message = render_to_string(
            'comments/emails/mention_notification.html', 
            context
        )
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[mentioned_user.email],
            fail_silently=True,
        )
    
    @staticmethod
    def highlight_mentions(comment_text):
        """Convert @username mentions to clickable links"""
        def replace_mention(match):
            username = match.group(1)
            try:
                user = User.objects.get(username=username)
                return f'<a href="/users/{username}/" class="user-mention">@{username}</a>'
            except User.DoesNotExist:
                return match.group(0)  # Return original if user doesn't exist
        
        return re.sub(r'@(\w+)', replace_mention, comment_text)