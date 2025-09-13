from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.cache import cache
from django.db import transaction
from django.http import Http404
from blogs.models import Blog, Category
import logging
from django.views.decorators.cache import never_cache, cache_control
from django.views.decorators.vary import vary_on_cookie
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)

@vary_on_cookie  # Cache differently for different users
@cache_control(private=True, max_age=0)  # Don't cache for authenticated users
def home(request):
    """
    Home page view with optimized queries and error handling
    """
    try:
        # Cache key for homepage data (cache for 15 minutes)
        cache_key = 'home_data'
        cached_data = cache.get(cache_key)
        
        if not cached_data:
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

            # Cache the data
            cached_data = {
                'featured_post': featured_post,
                'trending_posts': trending_posts,
                'editors_picks': editors_picks,
            }
            cache.set(cache_key, cached_data, 900)  # Cache for 15 minutes

        # Recent posts with pagination (don't cache paginated data)
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

        # Optimize category posts query with caching
        category_cache_key = 'category_posts_home'
        category_posts = cache.get(category_cache_key)
        
        if not category_posts:
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
            
            # Cache category posts for 30 minutes
            cache.set(category_cache_key, category_posts, 1800)

        context = {
            'featured_post': cached_data['featured_post'],
            'trending_posts': cached_data['trending_posts'],
            'editors_picks': cached_data['editors_picks'],
            'page_obj': page_obj,
            'category_posts': category_posts,
            'page_title': 'Home',
            'meta_description': 'Stay updated with the latest news, insights, and stories from our blog.',
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
        }
        return render(request, 'home.html', context)