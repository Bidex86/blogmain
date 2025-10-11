# ads/management/commands/setup_ad_positions.py
from django.core.management.base import BaseCommand
from ads.models import AdPosition

class Command(BaseCommand):
    help = 'Setup default ad positions'

    def handle(self, *args, **options):
        positions = [
            {
                'name': 'Header Banner',
                'slug': 'header-banner',
                'position_type': 'header',
                'width': 728,
                'height': 90,
                'description': 'Banner ad at the top of the page'
            },
            {
                'name': 'Sidebar Top',
                'slug': 'sidebar-top',
                'position_type': 'sidebar',
                'width': 300,
                'height': 250,
                'description': 'Medium rectangle in sidebar'
            },
            {
                'name': 'Sidebar Bottom',
                'slug': 'sidebar-bottom',
                'position_type': 'sidebar',
                'width': 300,
                'height': 600,
                'description': 'Half page ad in sidebar'
            },
            {
                'name': 'In Content',
                'slug': 'in-content',
                'position_type': 'in_content',
                'width': 336,
                'height': 280,
                'description': 'Large rectangle within content'
            },
            {
                'name': 'Between Posts',
                'slug': 'between-posts',
                'position_type': 'between_posts',
                'width': 728,
                'height': 90,
                'description': 'Banner between blog posts'
            },
            {
                'name': 'Footer Banner',
                'slug': 'footer-banner',
                'position_type': 'footer',
                'width': 728,
                'height': 90,
                'description': 'Banner at the bottom of the page'
            },
            {
                'name': 'Sticky Bottom',
                'slug': 'sticky-bottom',
                'position_type': 'sticky',
                'width': 320,
                'height': 100,
                'description': 'Sticky ad at bottom of screen'
            },
            {
                'name': 'Mobile Banner',
                'slug': 'mobile-banner',
                'position_type': 'header',
                'width': 320,
                'height': 50,
                'description': 'Mobile banner ad'
            },
        ]
        
        for pos_data in positions:
            position, created = AdPosition.objects.get_or_create(
                slug=pos_data['slug'],
                defaults=pos_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created ad position: {position.name}')
                )
            else:
                self.stdout.write(f'Ad position already exists: {position.name}')
