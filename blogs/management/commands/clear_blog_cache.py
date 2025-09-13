# Create these files in your Django app:
# blogs/management/commands/clear_blog_cache.py

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clear blog-related cache entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Clear all cache entries',
        )
        parser.add_argument(
            '--homepage',
            action='store_true',
            help='Clear homepage cache only',
        )

    def handle(self, *args, **options):
        if options['all']:
            cache.clear()
            self.stdout.write(
                self.style.SUCCESS('Successfully cleared all cache entries')
            )
            logger.info('All cache entries cleared')
            
        elif options['homepage']:
            cache_keys = ['homepage_data', 'category_posts_homepage']
            for key in cache_keys:
                cache.delete(key)
            self.stdout.write(
                self.style.SUCCESS('Successfully cleared homepage cache')
            )
            logger.info('Homepage cache cleared')
            
        else:
            # Clear specific blog cache patterns
            cache_patterns = [
                'homepage_data',
                'category_posts_homepage',
                'blog_*',
                'category_*',
            ]
            
            cleared_count = 0
            for pattern in cache_patterns:
                if '*' in pattern:
                    # For patterns with wildcards, you'd need django-redis
                    # or implement your own pattern matching
                    pass
                else:
                    if cache.delete(pattern):
                        cleared_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully cleared {cleared_count} cache entries')
            )
            logger.info(f'Cleared {cleared_count} blog cache entries')




# Usage instructions:
"""
To use these management commands:

1. Create the management/commands directories in your blogs app:
   mkdir -p blogs/management/commands
   touch blogs/management/__init__.py
   touch blogs/management/commands/__init__.py

2. Place each command in its respective file

3. Run the commands:
   python manage.py clear_blog_cache --homepage
   python manage.py warm_blog_cache
   python manage.py optimize_blog_images --quality=80 --max-width=1000
   python manage.py generate_sitemaps

4. Set up cron jobs for regular maintenance:
   # Clear and warm cache daily at 2 AM
   0 2 * * * /path/to/your/project/manage.py clear_blog_cache --all
   5 2 * * * /path/to/your/project/manage.py warm_blog_cache
   
   # Generate sitemaps weekly
   0 3 * * 0 /path/to/your/project/manage.py generate_sitemaps
"""