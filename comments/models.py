# comments/models.py - Fixed manager methods
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.conf import settings

class CommentManager(models.Manager):
    """Custom manager with useful methods"""
    
    def for_object(self, obj):
        """Get all comments for any object"""
        content_type = ContentType.objects.get_for_model(obj)
        return self.filter(content_type=content_type, object_id=obj.pk)
    
    def top_level_for_object(self, obj):
        """Get only parent comments (no replies) for an object"""
        return self.for_object(obj).filter(parent=None)
    
    def approved(self):
        """Get only approved comments"""
        return self.filter(is_approved=True)
    
    def pending_moderation(self):
        """Get comments awaiting moderation"""
        return self.filter(is_approved=False, is_flagged=False)

class Comment(models.Model):
    """
    Generic comment model that can attach to any Django model
    Supports nested replies with depth tracking
    """
    
    # Generic relationship - THIS IS THE KEY!
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Self-referencing for nested replies
    parent = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE, 
        related_name='children'
    )
    
    # Comment data
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField(
        max_length=getattr(settings, 'COMMENTS_MAX_LENGTH', 1000),
        help_text="Maximum 1000 characters"
    )
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    
    # Custom manager
    objects = CommentManager()
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            # Optimize queries for getting comments on objects
            models.Index(fields=['content_type', 'object_id', 'parent']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['is_approved', 'created_at']),
        ]
        
    def __str__(self):
        return f'Comment by {self.user.username} on {self.content_object}'
    
    def save(self, *args, **kwargs):
        """Custom save method to track edits"""
        if self.pk:  # If updating existing comment
            old_comment = Comment.objects.get(pk=self.pk)
            if old_comment.comment != self.comment:
                self.is_edited = True
        super().save(*args, **kwargs)
    
    @property
    def depth(self):
        """Calculate nesting depth (0 = top level, 1 = first reply, etc.)"""
        if not self.parent:
            return 0
        return self.parent.depth + 1
    
    @property 
    def max_depth_reached(self):
        """Check if maximum nesting depth is reached"""
        max_depth = getattr(settings, 'COMMENTS_MAX_DEPTH', 4)
        return self.depth >= max_depth
    
    def get_root_comment(self):
        """Get the top-level comment of this thread"""
        if not self.parent:
            return self
        return self.parent.get_root_comment()
    
    def can_be_edited_by(self, user):
        """Check if user can edit this comment"""
        if not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        if self.user != user:
            return False
            
        # Check time limit for editing
        edit_limit = getattr(settings, 'COMMENTS_EDIT_TIME_LIMIT', 15)
        if edit_limit:
            from datetime import timedelta
            deadline = self.created_at + timedelta(minutes=edit_limit)
            return timezone.now() <= deadline
        return True
    
class CommentFlag(models.Model):
    """Model for flagging inappropriate comments"""
    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('abuse', 'Abusive Language'),
        ('harassment', 'Harassment'),
        ('inappropriate', 'Inappropriate Content'),
        ('off_topic', 'Off Topic'),
        ('other', 'Other'),
    ]
    
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='flags')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(blank=True, help_text='Additional details about the flag')
    created_at = models.DateTimeField(default=timezone.now)
    is_reviewed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['comment', 'user']  # Prevent duplicate flags from same user
    
    def __str__(self):
        return f'Flag on comment {self.comment.id} by {self.user.username}'

class CommentLike(models.Model):
    """Model for liking/upvoting comments (optional feature)"""
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['comment', 'user']  # Prevent duplicate likes
    
    def __str__(self):
        return f'{self.user.username} likes comment {self.comment.id}'

# Remove the UserProfile class entirely to avoid conflicts with accounts.Profile