# comments/urls.py - Complete URL configuration
from django.urls import path
from . import views

app_name = 'comments'

urlpatterns = [
    # Basic comment operations
    path('add/', views.add_comment, name='add_comment'),
    path('<int:comment_id>/edit/', views.edit_comment, name='edit_comment'),
    path('<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('<int:comment_id>/flag/', views.flag_comment, name='flag_comment'),
    path('<int:comment_id>/like/', views.like_comment, name='like_comment'),
    
    # AJAX endpoints
    path('api/<int:comment_id>/replies/', views.get_comment_replies, name='comment_replies'),
    path('api/search/', views.search_comments, name='search_comments'),
    path('api/load-more/', views.load_more_comments, name='load_more_comments'),
    path('api/stats/', views.comment_stats, name='comment_stats'),
    path('api/post/<int:post_id>/stats/', views.comment_stats, name='post_comment_stats'),
    
    # User comment management
    path('my-comments/', views.user_comments, name='user_comments'),
    
    # Moderation URLs (admin/staff only)
    path('admin/moderate/', views.moderate_comments, name='moderate_comments'),
    path('admin/<int:comment_id>/moderate/', views.moderate_comment, name='moderate_comment'),
    path('admin/flags/', views.view_flags, name='view_flags'),
    path('admin/flag/<int:flag_id>/review/', views.mark_flag_reviewed, name='mark_flag_reviewed'),
]