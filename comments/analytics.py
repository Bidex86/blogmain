# comments/analytics.py
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Comment

class CommentAnalytics:
    """Analytics for comment system"""
    
    @staticmethod
    def get_engagement_stats(obj):
        """Get engagement statistics for an object"""
        comments = Comment.objects.for_object(obj)
        
        return {
            'total_comments': comments.count(),
            'unique_commenters': comments.values('user').distinct().count(),
            'avg_comments_per_user': comments.count() / max(comments.values('user').distinct().count(), 1),
            'reply_percentage': (comments.filter(parent__isnull=False).count() / max(comments.count(), 1)) * 100,
            'most_active_commenter': comments.values('user__username').annotate(
                count=Count('id')
            ).order_by('-count').first(),
        }
    
    @staticmethod
    def get_trending_objects():
        """Get objects with most comments in last 24 hours"""
        yesterday = timezone.now() - timedelta(days=1)
        
        trending = Comment.objects.filter(
            created_at__gte=yesterday
        ).values(
            'content_type__model', 'object_id'
        ).annotate(
            comment_count=Count('id')
        ).order_by('-comment_count')[:10]
        
        return trending
    
    @staticmethod
    def get_user_comment_stats(user):
        """Get comment statistics for a specific user"""
        user_comments = Comment.objects.filter(user=user)
        
        return {
            'total_comments': user_comments.count(),
            'total_replies': user_comments.filter(parent__isnull=False).count(),
            'comments_received': Comment.objects.filter(parent__user=user).count(),
            'avg_comment_length': user_comments.aggregate(
                avg_length=Avg('comment__length')
            )['avg_length'] or 0,
            'most_commented_object': user_comments.values(
                'content_type__model', 'object_id'
            ).annotate(
                count=Count('id')
            ).order_by('-count').first(),
        }