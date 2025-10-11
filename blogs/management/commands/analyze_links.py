from django.core.management.base import BaseCommand
from blogs.models import Blog
from blogs.link_building import AILinkBuilder

class Command(BaseCommand):
    help = 'Analyze blog posts for link building opportunities'
    
    def add_arguments(self, parser):
        parser.add_argument('--post-id', type=int, help='Analyze specific post')
        parser.add_argument('--all', action='store_true', help='Analyze all posts')
        parser.add_argument('--check-broken', action='store_true', help='Check for broken links')
    
    def handle(self, *args, **options):
        link_builder = AILinkBuilder()
        
        if options['post_id']:
            try:
                post = Blog.objects.get(id=options['post_id'])
                self.analyze_post(post, link_builder, options['check_broken'])
            except Blog.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Post {options["post_id"]} not found'))
        
        elif options['all']:
            posts = Blog.objects.filter(status='Published')
            for post in posts:
                self.analyze_post(post, link_builder, options['check_broken'])
        
        else:
            self.stdout.write(self.style.WARNING('Specify --post-id or --all'))
    
    def analyze_post(self, post, link_builder, check_broken=False):
        self.stdout.write(f'\n--- Analyzing: {post.title} ---')
        
        # Get link suggestions
        suggestions = link_builder.generate_link_suggestions(post)
        
        # Internal links
        internal_links = suggestions['internal_links']
        if internal_links:
            self.stdout.write(f'\nInternal Link Opportunities ({len(internal_links)}):')
            for opportunity in internal_links[:5]:  # Show top 5
                self.stdout.write(f'  → {opportunity["target_post"].title}')
                self.stdout.write(f'    Anchor: "{opportunity["anchor_text"]}"')
                self.stdout.write(f'    Score: {opportunity["relevance_score"]:.2f}')
        
        # Broken links
        if check_broken:
            broken_links = suggestions['broken_links']
            if broken_links:
                self.stdout.write(f'\nBroken Links ({len(broken_links)}):')
                for link in broken_links:
                    self.stdout.write(
                        self.style.ERROR(f'  ✗ {link["url"]} - {link["error_message"]}')
                    )
        
        # Anchor text analysis
        anchor_analysis = suggestions['anchor_optimization']
        if anchor_analysis['suggestions']:
            self.stdout.write(f'\nAnchor Text Suggestions:')
            for suggestion in anchor_analysis['suggestions']:
                self.stdout.write(f'  • {suggestion.get("message", suggestion.get("suggestion", ""))}')