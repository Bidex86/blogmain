from django.urls import path
from . import views
from django.contrib.sitemaps.views import sitemap
from .sitemaps import BlogSitemap

sitemaps = {
    'blogs': BlogSitemap,
}

urlpatterns = [
     path('category/<slug:category_slug>/', views.posts_by_category, name="posts_by_category"),
     path('tag/<slug:tag_slug>/', views.tagged_posts, name='tagged_posts'),
     path('tags/suggestions/', views.tag_suggestions, name='tag_suggestions'),
     path("sitemap.xml", sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
     path("robots.txt", views.robots_txt),

]
