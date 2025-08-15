from django.contrib.sitemaps import Sitemap
from .models import Blog  # or your blog post model

class BlogSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Blog.objects.all()

    def lastmod(self, obj):
        return obj.updated_at  # or `created_at` if no updated field
    
