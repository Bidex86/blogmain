# blogs/management/commands/warm_blog_cache.py

from django.core.management.base import BaseCommand
from django.core.cache import cache
from blogs.models import Blog, Category
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Warm up blog cache with frequently accessed data'

    def handle(self, *args, **options):
        self.stdout.write('Starting cache warming...')
        
        try:
            # Warm homepage data cache
            self.warm_homepage_cache()
            
            # Warm category cache
            self.warm_category_cache()
            
            self.stdout.write(
                self.style.SUCCESS('Successfully warmed blog cache')
            )
            logger.info('Blog cache warming completed successfully')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error warming cache: {str(e)}')
            )
            logger.error(f'Cache warming failed: {str(e)}')

    def warm_homepage_cache(self):
        """Warm homepage-related cache"""
        published_posts = Blog.objects.select_related('category').filter(status='Published')
        
        # Featured post
        featured_post = published_posts.filter(is_featured=True).order_by('-created_at').first()
        if not featured_post:
            featured_post = published_posts.order_by('-created_at').first()

        # Trending posts
        trending_posts = list(published_posts.order_by('-views')[:2])

        # Editor's picks
        editors_picks = list(published_posts.filter(is_editors_pick=True).order_by('-created_at')[:5])
        if not editors_picks:
            editors_picks = list(published_posts.order_by('-created_at')[1:6])

        # Cache the data
        cached_data = {
            'featured_post': featured_post,
            'trending_posts': trending_posts,
            'editors_picks': editors_picks,
        }
        cache.set('homepage_data', cached_data, 900)
        self.stdout.write('✓ Homepage data cached')

    def warm_category_cache(self):
        """Warm category-related cache"""
        categories = Category.objects.prefetch_related('blog_set__category').filter(
            blog__status='Published'
        ).distinct()
        
        category_posts = {}
        for category in categories:
            posts_for_category = list(
                category.blog_set
                .select_related('category')
                .filter(status='Published')
                .order_by('-created_at')[:6]
            )
            if posts_for_category:
                category_posts[category] = posts_for_category

        cache.set('category_posts_homepage', category_posts, 1800)
        self.stdout.write(f'✓ Category data cached for {len(category_posts)} categories')