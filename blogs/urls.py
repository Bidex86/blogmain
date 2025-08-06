from django.urls import path
from . import views

urlpatterns = [
     path('category/<slug:category_slug>/', views.posts_by_category, name="posts_by_category"),
     path('tag/<slug:tag_slug>/', views.tagged_posts, name='tagged_posts'),
     path('tags/suggestions/', views.tag_suggestions, name='tag_suggestions'),
]
