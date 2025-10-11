from django.db import models
from django.contrib.auth.models import User
from blogs.models import Category
# Create your models here.


class PushSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    subscription_info = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('user', 'subscription_info')
    
    def __str__(self):
        return f"{self.user.username} - {self.created_at}"
    
class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference')
    
    # Notification types
    notify_new_posts = models.BooleanField(default=True)
    notify_comments = models.BooleanField(default=True)
    notify_comment_replies = models.BooleanField(default=True)
    notify_system = models.BooleanField(default=True)
    
    # Category preferences
    categories = models.ManyToManyField(Category, blank=True, related_name='notification_subscribers')
    
    # Notification methods
    push_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s preferences"
    
    def should_notify_for_category(self, category):
        """Check if user wants notifications for this category"""
        if not self.categories.exists():
            return True  # If no categories selected, notify for all
        return self.categories.filter(id=category.id).exists()


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('new_post', 'New Post'),
        ('new_comment', 'New Comment'),
        ('comment_reply', 'Comment Reply'),
        ('system', 'System Notification'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    url = models.CharField(max_length=500, blank=True)
    
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    
    # Optional: Link to related objects
    blog_post = models.ForeignKey('blogs.Blog', null=True, blank=True, on_delete=models.CASCADE)
    comment = models.ForeignKey('comments.Comment', null=True, blank=True, on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"