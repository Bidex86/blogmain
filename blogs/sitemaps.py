from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Blog, Category

class BlogSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    protocol = 'https'  # Change to https in production

    def items(self):
        return Blog.objects.filter(status='Published').order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return obj.get_absolute_url()

class CategorySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6
    protocol = 'https'  # Change to https in production
    
    def items(self):
        return Category.objects.all()
    
    def lastmod(self, obj):
        # Get the most recent post in this category
        latest_post = Blog.objects.filter(
            category=obj, 
            status='Published'
        ).order_by('-updated_at').first()
        return latest_post.updated_at if latest_post else obj.updated_at
    
    def location(self, obj):
        return obj.get_absolute_url()

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'
    protocol = 'https'  # Change to https in production

    def items(self):
        return ['home']

    def location(self, item):
        return reverse(item)