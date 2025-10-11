from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Blog, Category
import xml.etree.ElementTree as ET
from django.http import HttpResponse
from django.conf import settings

# Your existing classes remain the same
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

# NEW: News Sitemap Class
class NewsSitemap:
    """Google News Sitemap Generator - compatible with your existing setup"""
    
    def __init__(self):
        self.protocol = 'https'  # Change based on your setup
        self.max_articles = 1000  # Google News limit
        self.days_back = 2  # Only include articles from last 2 days
    
    def get_news_articles(self):
        """Get recent articles for news sitemap"""
        cutoff_date = timezone.now() - timedelta(days=self.days_back)
        
        # Check if you have news-specific fields, otherwise use category filtering
        try:
            # Try with news-specific fields (if you've added them)
            return Blog.objects.filter(
                status='Published',
                created_at__gte=cutoff_date,
                exclude_from_news=False  # Only if this field exists
            ).select_related('category', 'author').order_by('-created_at')[:self.max_articles]
        except:
            # Fallback to category-based filtering (works with your current setup)
            return Blog.objects.filter(
                status='Published',
                created_at__gte=cutoff_date,
                # Only include posts with news-worthy categories
                category__category_name__in=[
                    'News', 'Breaking News', 'Current Events', 'Technology News',
                    'Business News', 'Politics', 'Health News', 'Sports News',
                    'Entertainment News', 'Science News', 'Tech', 'Technology'
                ]
            ).select_related('category', 'author').order_by('-created_at')[:self.max_articles]
    
    def generate_news_sitemap_xml(self):
        """Generate Google News sitemap XML"""
        # Create root element with proper namespaces
        root = ET.Element('urlset')
        root.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')
        root.set('xmlns:news', 'http://www.google.com/schemas/sitemap-news/0.9')
        root.set('xmlns:image', 'http://www.google.com/schemas/sitemap-image/1.1')
        
        articles = self.get_news_articles()
        
        for article in articles:
            # Create URL element
            url_elem = ET.SubElement(root, 'url')
            
            # Add location - using your existing URL structure
            loc_elem = ET.SubElement(url_elem, 'loc')
            loc_elem.text = f"{self.protocol}://yourdomain.com{article.get_absolute_url()}"
            
            # Add news-specific data
            news_elem = ET.SubElement(url_elem, 'news:news')
            
            # Publication info
            publication_elem = ET.SubElement(news_elem, 'news:publication')
            
            pub_name_elem = ET.SubElement(publication_elem, 'news:name')
            pub_name_elem.text = getattr(settings, 'SITE_NAME', 'Your Blog Name')
            
            pub_lang_elem = ET.SubElement(publication_elem, 'news:language')
            pub_lang_elem.text = getattr(settings, 'LANGUAGE_CODE', 'en')[:2]
            
            # Article info
            publication_date_elem = ET.SubElement(news_elem, 'news:publication_date')
            # Handle timezone formatting
            if hasattr(article.created_at, 'strftime'):
                if article.created_at.tzinfo:
                    publication_date_elem.text = article.created_at.strftime('%Y-%m-%dT%H:%M:%S%z')
                else:
                    publication_date_elem.text = article.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            title_elem = ET.SubElement(news_elem, 'news:title')
            title_elem.text = article.title
            
            # Add keywords from tags (works with your existing taggit setup)
            if hasattr(article, 'tags') and article.tags.exists():
                keywords_elem = ET.SubElement(news_elem, 'news:keywords')
                keywords_elem.text = ', '.join([tag.name for tag in article.tags.all()[:10]])
            
            # Add genres - try news_genre field, fallback to category
            try:
                if hasattr(article, 'news_genre') and article.news_genre:
                    genres_elem = ET.SubElement(news_elem, 'news:genres')
                    genres_elem.text = article.news_genre
                else:
                    # Map category to news genre
                    category_to_genre = {
                        'Breaking News': 'PressRelease',
                        'News': 'PressRelease',
                        'Politics': 'PressRelease',
                        'Business News': 'PressRelease',
                        'Technology': 'Blog',
                        'Tech': 'Blog',
                        'Opinion': 'Opinion',
                        'Entertainment': 'Blog'
                    }
                    genre = category_to_genre.get(article.category.category_name, 'Blog')
                    genres_elem = ET.SubElement(news_elem, 'news:genres')
                    genres_elem.text = genre
            except:
                pass  # Skip if no genre mapping
            
            # Add image information if featured image exists
            if hasattr(article, 'featured_image') and article.featured_image:
                try:
                    image_elem = ET.SubElement(url_elem, 'image:image')
                    
                    image_loc_elem = ET.SubElement(image_elem, 'image:loc')
                    image_loc_elem.text = f"{self.protocol}://yourdomain.com{article.featured_image.url}"
                    
                    # Use image_alt_text if available, otherwise use title
                    image_caption = getattr(article, 'image_alt_text', None) or article.title
                    image_caption_elem = ET.SubElement(image_elem, 'image:caption')
                    image_caption_elem.text = image_caption
                    
                    image_title_elem = ET.SubElement(image_elem, 'image:title')
                    image_title_elem.text = article.title
                except:
                    pass  # Skip image if there's an error
        
        return ET.tostring(root, encoding='unicode', method='xml')
