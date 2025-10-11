from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.cache import cache
from django.db import transaction
from django.http import Http404
from blogs.models import Blog, Category
import logging
from django.conf import settings
from django.template.loader import render_to_string
import json
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)

def home(request):
    """
    Home page view with optimized queries and error handling
    Note: Caching is now handled by AuthAwareCacheMiddleware
    """
    # Add debugging to see user state
    print(f"HOME VIEW - User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    print(f"HOME VIEW - Authenticated: {request.user.is_authenticated}")
    
    try:
        # Use select_related for all queries to reduce database hits
        published_posts = Blog.objects.select_related('category').filter(status='Published')
        
        # Featured post - get the most recent featured post
        featured_post = published_posts.filter(is_featured=True).order_by('-created_at').first()
        
        # If no featured post, use the most recent post
        if not featured_post:
            featured_post = published_posts.order_by('-created_at').first()

        # Trending posts (most viewed) - ensure we have posts
        trending_posts = published_posts.order_by('-views')[:2]

        # Editor's picks - fallback to recent posts if no editor picks
        editors_picks = published_posts.filter(is_editors_pick=True).order_by('-created_at')[:5]
        if not editors_picks.exists():
            editors_picks = published_posts.order_by('-created_at')[1:6]  # Skip featured post

        # Recent posts with pagination
        posts = Blog.objects.select_related('category').filter(status='Published').order_by('-created_at')
        paginator = Paginator(posts, 10)
        page_number = request.GET.get('page', 1)
        
        try:
            page_number = int(page_number)
            if page_number < 1:
                page_number = 1
        except (ValueError, TypeError):
            page_number = 1
            
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        # Category posts query
        categories = Category.objects.prefetch_related(
            'blog_set__category'
        ).filter(blog__status='Published').distinct()
        
        category_posts = {}
        
        for category in categories:
            # Get published posts for this category
            posts_for_category = (
                category.blog_set
                .select_related('category')
                .filter(status='Published')
                .order_by('-created_at')[:6]
            )
            if posts_for_category:  # Only include categories with posts
                category_posts[category] = posts_for_category

        context = {
            'featured_post': featured_post,
            'trending_posts': trending_posts,
            'editors_picks': editors_picks,
            'page_obj': page_obj,
            'category_posts': category_posts,
            'page_title': 'Home',
            'meta_description': 'Stay updated with the latest news, insights, and stories from our blog.',
            'user': request.user,  # Explicitly pass user context
        }
        
        return render(request, 'home.html', context)
        
    except Exception as e:
        logger.error(f"Error in home view: {str(e)}")
        # Return a minimal context to prevent complete failure
        context = {
            'featured_post': None,
            'trending_posts': [],
            'editors_picks': [],
            'page_obj': None,
            'category_posts': {},
            'error_message': 'Some content may be temporarily unavailable.',
            'user': request.user,  # Make sure user context is always available
        }
        return render(request, 'home.html', context)
    
def manifest(request):
    """Generate PWA manifest"""
    manifest_data = {
        "name": settings.PWA_CONFIG['name'],
        "short_name": settings.PWA_CONFIG['short_name'],
        "description": settings.PWA_CONFIG['description'],
        "start_url": settings.PWA_CONFIG['start_url'],
        "display": settings.PWA_CONFIG['display'],
        "theme_color": settings.PWA_CONFIG['theme_color'],
        "background_color": settings.PWA_CONFIG['background_color'],
        "icons": settings.PWA_CONFIG['icons']
    }
    
    return JsonResponse(manifest_data)

def service_worker(request):
    """Serve the service worker"""
    # In production, serve this as a static file
    content = render_to_string('pwa/sw.js', {
        'cache_name': 'blog-pwa-v1.0.0',
        'static_urls': [
            '{% load pipeline %}{% stylesheet_url "main" %}', # This will resolve to /static/css/main.min.css (or versioned filename)
            '{% load pipeline %}{% javascript_url "main" %}', # This will resolve to /static/js/main.min.js (or versioned filename)
            '/static/images/logo.png',
            '/static/images/placeholder.jpg',
            '/offline/',
            '/manifest.json'
        ]
    })
    
    return HttpResponse(content, content_type='application/javascript')

def offline_page(request):
    """Offline page for PWA"""
    return render(request, 'pwa/offline.html')

def robots_txt(request):
    """Generate robots.txt"""
    lines = [
        "User-Agent: *",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /dashboard/",
        "Allow: /",
        "",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
