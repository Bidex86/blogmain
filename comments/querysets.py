# comments/querysets.py
from django.db.models import Prefetch
from .models import Comment

def get_optimized_comments(obj):
    """Get comments with optimized queries to reduce database hits"""
    
    # Prefetch nested replies up to 3 levels deep
    level_1_prefetch = Prefetch(
        'children',
        queryset=Comment.objects.select_related('user', 'user__profile')
    )
    
    level_2_prefetch = Prefetch(
        'children__children',
        queryset=Comment.objects.select_related('user', 'user__profile')
    )
    
    level_3_prefetch = Prefetch(
        'children__children__children',
        queryset=Comment.objects.select_related('user', 'user__profile')
    )
    
    return Comment.objects.top_level_for_object(obj).select_related(
        'user', 'user__profile'
    ).prefetch_related(
        level_1_prefetch,
        level_2_prefetch, 
        level_3_prefetch
    ).approved()