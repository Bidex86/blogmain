from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    newsletter_opt_in = models.BooleanField(default=False)
    
    # Add avatar field
    avatar = models.ImageField(
        upload_to='avatars/', 
        null=True, 
        blank=True,
        help_text='Upload a profile picture'
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    email_on_reply = models.BooleanField(
        default=True, 
        help_text='Receive email when someone replies to your comment'
    )
    email_on_mention = models.BooleanField(
        default=True, 
        help_text='Receive email when mentioned in a comment'
    )
    is_comment_moderator = models.BooleanField(default=False)
    comment_ban_until = models.DateTimeField(
        null=True, 
        blank=True,
        help_text='User is banned from commenting until this date'
    )
    
    # Add this method to your existing Profile model:
    @property
    def is_comment_banned(self):
        """Check if user is currently banned from commenting"""
        if not self.comment_ban_until:
            return False
        from django.utils import timezone
        return timezone.now() < self.comment_ban_until
    
    # Updated get_avatar_url method:
    def get_avatar_url(self):
        """Get avatar URL or return default"""
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return '/static/images/default-avatar.png'