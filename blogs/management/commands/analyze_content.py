from django.core.management.base import BaseCommand
from blogs.models import Blog
from blogs.ai_content import AIContentIntelligence

class Command(BaseCommand):
    help = 'Analyze blog content using AI intelligence'
    
    def add_arguments(self, parser):
        parser.add_argument('--blog-id', type=int, help='Analyze specific blog post')
        parser.add_argument('--all', action='store_true', help='Analyze all published posts')
    
    def handle(self, *args, **options):
        if options['blog_id']:
            try:
                blog = Blog.objects.get(id=options['blog_id'])
                self.analyze_single_blog(blog)
            except Blog.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Blog with ID {options["blog_id"]} not found'))
        
        elif options['all']:
            blogs = Blog.objects.filter(status='Published')
            self.stdout.write(f'Analyzing {blogs.count()} blog posts...')
            
            for blog in blogs:
                self.analyze_single_blog(blog)
                
        else:
            self.stdout.write(self.style.WARNING('Please specify --blog-id or --all'))
    
    def analyze_single_blog(self, blog):
        ai_analyzer = AIContentIntelligence(blog)
        analysis = ai_analyzer.analyze_content()
        
        self.stdout.write(f'\n--- Analysis for: {blog.title} ---')
        self.stdout.write(f'Overall Score: {analysis["score"]}/100')
        self.stdout.write(f'Readability Grade: {analysis["readability"]["readability_grade"]}')
        self.stdout.write(f'Word Count: {analysis["readability"]["word_count"]}')
        self.stdout.write(f'SEO Score Factors:')
        self.stdout.write(f'  - Keyword Density: {analysis["seo"]["keyword_density"]}%')
        self.stdout.write(f'  - Title Length: {analysis["seo"]["title_optimization"]["length"]} chars')
        self.stdout.write(f'  - Meta Description: {analysis["seo"]["meta_description"]["length"]} chars')
        
        if analysis['suggestions']:
            self.stdout.write(f'\nSuggestions:')
            for suggestion in analysis['suggestions']:
                priority_color = self.style.ERROR if suggestion['priority'] == 'high' else self.style.WARNING
                self.stdout.write(priority_color(f'  [{suggestion["priority"].upper()}] {suggestion["message"]}'))
                self.stdout.write(f'    Action: {suggestion["action"]}')