# comments/admin.py (additional features)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import Comment, CommentFlag

class CommentAdmin(admin.ModelAdmin):
    # ... existing code ...
    
    # Advanced filters
    list_filter = (
        'is_approved', 
        'is_flagged', 
        'is_edited',
        'created_at',
        ('content_type', admin.RelatedOnlyFieldListFilter),
        ('user', admin.RelatedOnlyFieldListFilter),
    )
    
    # Custom admin actions
    actions = [
        'approve_comments', 
        'flag_comments', 
        'bulk_delete_spam',
        'export_comments_csv'
    ]
    
    def bulk_delete_spam(self, request, queryset):
        """Delete comments marked as spam"""
        spam_count = 0
        for comment in queryset:
            if self.is_likely_spam(comment):
                comment.delete()
                spam_count += 1
        
        self.message_user(
            request, 
            f'Deleted {spam_count} spam comments.',
            messages.SUCCESS
        )
    bulk_delete_spam.short_description = 'Delete spam comments'
    
    def export_comments_csv(self, request, queryset):
        """Export selected comments to CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="comments.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'User', 'Content Object', 'Comment', 'Created', 'Is Reply'])
        
        for comment in queryset:
            writer.writerow([
                comment.id,
                comment.user.username,
                str(comment.content_object),
                comment.comment[:100],
                comment.created_at.strftime('%Y-%m-%d %H:%M'),
                'Yes' if comment.parent else 'No'
            ])
        
        return response
    export_comments_csv.short_description = 'Export to CSV'
    
    def is_likely_spam(self, comment):
        """Check if comment is likely spam"""
        from .utils import detect_spam_content
        return detect_spam_content(comment.comment)
    
    # Custom admin URLs
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('stats/', self.admin_site.admin_view(self.stats_view), name='comment_stats'),
            path('moderation/', self.admin_site.admin_view(self.moderation_view), name='comment_moderation'),
        ]
        return custom_urls + urls
    
    def stats_view(self, request):
        """Custom admin view for comment statistics"""
        from django.db.models import Count, Q
        from datetime import timedelta
        from django.utils import timezone
        
        # Calculate statistics
        total_comments = Comment.objects.count()
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        stats = {
            'total_comments': total_comments,
            'approved_comments': Comment.objects.filter(is_approved=True).count(),
            'pending_comments': Comment.objects.filter(is_approved=False).count(),
            'flagged_comments': Comment.objects.filter(is_flagged=True).count(),
            'this_week': Comment.objects.filter(created_at__gte=week_ago).count(),
            'top_commenters': Comment.objects.values('user__username').annotate(
                count=Count('id')
            ).order_by('-count')[:10],
        }
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Comment Statistics',
            'stats': stats,
        }
        
        return render(request, 'admin/comments/stats.html', context)