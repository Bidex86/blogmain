# blogs/management/commands/generate_sitemaps.py

from django.core.management.base import BaseCommand
from django.contrib.sitemaps import GenericSitemap
from blogs.models import Blog, Category
from django.urls import reverse
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Generate XML sitemaps for better SEO'

    def handle(self, *args, **options):
        self.stdout.write('Generating sitemaps...')
        
        try:
            # Generate main sitemap
            self.generate_main_sitemap()
            
            # Generate blog posts sitemap
            self.generate_posts_sitemap()
            
            # Generate categories sitemap
            self.generate_categories_sitemap()
            
            self.stdout.write(
                self.style.SUCCESS('Successfully generated sitemaps')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating sitemaps: {str(e)}')
            )

    def generate_main_sitemap(self):
        """Generate main sitemap index"""
        root = ET.Element('sitemapindex')
        root.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        # Add sub-sitemaps
        sitemaps = [
            ('sitemap-posts.xml', datetime.now()),
            ('sitemap-categories.xml', datetime.now()),
        ]
        
        for sitemap_url, lastmod in sitemaps:
            sitemap_elem = ET.SubElement(root, 'sitemap')
            ET.SubElement(sitemap_elem, 'loc').text = f'https://yourdomain.com/{sitemap_url}'
            ET.SubElement(sitemap_elem, 'lastmod').text = lastmod.strftime('%Y-%m-%d')
        
        self.save_sitemap('sitemap.xml', root)

    def generate_posts_sitemap(self):
        """Generate sitemap for blog posts"""
        root = ET.Element('urlset')
        root.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        posts = Blog.objects.filter(status='Published').order_by('-updated_at')
        
        for post in posts:
            url_elem = ET.SubElement(root, 'url')
            ET.SubElement(url_elem, 'loc').text = f'https://yourdomain.com/blog/{post.category.slug}/{post.slug}/'
            ET.SubElement(url_elem, 'lastmod').text = post.updated_at.strftime('%Y-%m-%d')
            ET.SubElement(url_elem, 'changefreq').text = 'weekly'
            ET.SubElement(url_elem, 'priority').text = '0.8'
        
        self.save_sitemap('sitemap-posts.xml', root)

    def generate_categories_sitemap(self):
        """Generate sitemap for categories"""
        root = ET.Element('urlset')
        root.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        
        categories = Category.objects.filter(blog__status='Published').distinct()
        
        for category in categories:
            url_elem = ET.SubElement(root, 'url')
            ET.SubElement(url_elem, 'loc').text = f'https://yourdomain.com/category/{category.slug}/'
            ET.SubElement(url_elem, 'lastmod').text = datetime.now().strftime('%Y-%m-%d')
            ET.SubElement(url_elem, 'changefreq').text = 'daily'
            ET.SubElement(url_elem, 'priority').text = '0.6'
        
        self.save_sitemap('sitemap-categories.xml', root)

    def save_sitemap(self, filename, root):
        """Save sitemap to file"""
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        
        sitemap_path = os.path.join(settings.STATIC_ROOT or settings.BASE_DIR, filename)
        tree.write(sitemap_path, encoding='utf-8', xml_declaration=True)
        
        self.stdout.write(f'✓ Generated {filename}')
