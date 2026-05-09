# comments/admin.py - Complete version
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import Comment, CommentFlag, CommentLike


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'user_link', 
        'comment_preview', 
        'content_object_link',
        'created_at', 
        'is_approved', 
        'is_flagged',
        'reply_count',
        'like_count'
    ]
    
    list_filter = [
        'is_approved', 
        'is_flagged', 
        'is_edited',
        'created_at',
        'content_type',
    ]
    
    search_fields = [
        'comment', 
        'user__username',
        'user__email'
    ]
    
    readonly_fields = [
        'content_type', 
        'object_id', 
        'created_at', 
        'updated_at',
        'depth'
    ]
    
    actions = [
        'approve_comments', 
        'flag_comments',
        'unflag_comments',
        'delete_selected_comments'
    ]
    
    date_hierarchy = 'created_at'
    
    def comment_preview(self, obj):
        """Show preview of comment"""
        preview = obj.comment[:75] + '...' if len(obj.comment) > 75 else obj.comment
        return preview
    comment_preview.short_description = 'Comment'
    
    def user_link(self, obj):
        """Link to user in admin"""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def content_object_link(self, obj):
        """Link to content object"""
        try:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.content_object.get_absolute_url(),
                str(obj.content_object)[:50]
            )
        except:
            return str(obj.content_object)[:50]
    content_object_link.short_description = 'On'
    
    def reply_count(self, obj):
        """Show number of replies"""
        count = obj.children.count()
        if count > 0:
            return format_html('<span style="color: #28a745;">{}</span>', count)
        return '0'
    reply_count.short_description = 'Replies'
    
    def like_count(self, obj):
        """Show number of likes"""
        count = obj.likes.count()
        if count > 0:
            return format_html('<span style="color: #007bff;">{}</span>', count)
        return '0'
    like_count.short_description = 'Likes'
    
    def approve_comments(self, request, queryset):
        """Bulk approve comments"""
        updated = queryset.update(is_approved=True, is_flagged=False)
        self.message_user(request, f'{updated} comments approved.')
    approve_comments.short_description = 'Approve selected comments'
    
    def flag_comments(self, request, queryset):
        """Bulk flag comments"""
        updated = queryset.update(is_flagged=True)
        self.message_user(request, f'{updated} comments flagged.')
    flag_comments.short_description = 'Flag selected comments'
    
    def unflag_comments(self, request, queryset):
        """Bulk unflag comments"""
        updated = queryset.update(is_flagged=False)
        self.message_user(request, f'{updated} comments unflagged.')
    unflag_comments.short_description = 'Unflag selected comments'
    
    def delete_selected_comments(self, request, queryset):
        """Bulk delete with confirmation"""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} comments deleted.')
    delete_selected_comments.short_description = 'Delete selected comments'
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'content_type').prefetch_related('children', 'likes')


@admin.register(CommentFlag)
class CommentFlagAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'comment_preview',
        'flagged_by',
        'reason',
        'created_at',
        'is_reviewed'
    ]
    
    list_filter = [
        'reason',
        'is_reviewed',
        'created_at'
    ]
    
    search_fields = [
        'comment__comment',
        'user__username',
        'description'
    ]
    
    readonly_fields = ['comment', 'user', 'created_at']
    
    actions = ['mark_as_reviewed', 'mark_as_unreviewed']
    
    def comment_preview(self, obj):
        """Show preview of flagged comment"""
        preview = obj.comment.comment[:50] + '...' if len(obj.comment.comment) > 50 else obj.comment.comment
        return preview
    comment_preview.short_description = 'Comment'
    
    def flagged_by(self, obj):
        """Show who flagged the comment"""
        return obj.user.username
    flagged_by.short_description = 'Flagged By'
    flagged_by.admin_order_field = 'user__username'
    
    def mark_as_reviewed(self, request, queryset):
        """Mark flags as reviewed"""
        updated = queryset.update(is_reviewed=True)
        self.message_user(request, f'{updated} flags marked as reviewed.')
    mark_as_reviewed.short_description = 'Mark as reviewed'
    
    def mark_as_unreviewed(self, request, queryset):
        """Mark flags as unreviewed"""
        updated = queryset.update(is_reviewed=False)
        self.message_user(request, f'{updated} flags marked as unreviewed.')
    mark_as_unreviewed.short_description = 'Mark as unreviewed'


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user_link',
        'comment_preview',
        'created_at'
    ]
    
    list_filter = ['created_at']
    
    search_fields = [
        'user__username',
        'comment__comment'
    ]
    
    readonly_fields = ['comment', 'user', 'created_at']
    
    def user_link(self, obj):
        """Link to user"""
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def comment_preview(self, obj):
        """Show comment preview"""
        preview = obj.comment.comment[:50] + '...' if len(obj.comment.comment) > 50 else obj.comment.comment
        return preview
    comment_preview.short_description = 'Comment'