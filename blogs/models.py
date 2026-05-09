from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from django.urls import reverse
from taggit.managers import TaggableManager
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
import os
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


# Create your models here.
class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    # SEO fields for categories
    meta_title = models.CharField(max_length=60, blank=True, help_text="SEO title (60 chars max)")
    meta_description = models.TextField(max_length=160, blank=True, help_text="SEO description (160 chars max)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.category_name)
        super().save(*args, **kwargs)    

    def get_absolute_url(self):
        return reverse('posts_by_category', kwargs={'category_slug': self.slug})

    def get_meta_title(self):
        return self.meta_title or f"{self.category_name} - Latest Articles"
    
    def get_meta_description(self):
        return self.meta_description or f"Browse all {self.category_name.lower()} articles and stay updated with the latest news."

    def __str__(self):
        return self.category_name


STATUS_CHOICES =(
    ("Draft", "Draft"),
    ("Published", "Published")
)

# NEW: Content type choices
CONTENT_TYPE_CHOICES = [
    ('article', 'Article'),
    ('video', 'Video'),
    ('mixed', 'Article with Video'),
]

def validate_image_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png']
    if ext not in valid_extensions:
        raise ValidationError('Only .jpg, .jpeg, .png images are allowed')

class Blog(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    
    # NEW: Content type field
    content_type = models.CharField(
        max_length=10,
        choices=CONTENT_TYPE_CHOICES,
        default='article',
        help_text='Type of content (auto-detected based on video)'
    )
    
    # SEO Enhancement Fields
    meta_title = models.CharField(max_length=60, blank=True, help_text="SEO title (60 chars max)")
    meta_description = CKEditor5Field('Description', config_name='default')
    focus_keyword = models.CharField(max_length=100, blank=True, help_text="Main SEO keyword for this post")
    seo_keywords = models.CharField(max_length=255, blank=True, help_text="Comma-separated keywords for auto-linking")
    
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    featured_image = models.ImageField(upload_to='uploads/%Y/%m/%d', validators=[validate_image_extension])
    image_alt_text = models.CharField(max_length=125, blank=True, help_text="Alt text for featured image (SEO)")
    image_base_name = models.CharField(max_length=255, blank=True, help_text="SEO_friendly base name for the feautred image (auto fill)", editable=False)
    image_width = models.PositiveIntegerField(blank=True, null=True, help_text="Original image width in pixels.", editable=True)
    image_height = models.PositiveIntegerField(blank=True, null=True, help_text="Original image height in pixels.", editable=False)
    short_description = CKEditor5Field('Description', config_name='default')
    blog_body = CKEditor5Field('Content', config_name='default')
    
    # NEW: Video fields
    video_file = models.FileField(
        upload_to='blog_videos/%Y/%m/%d/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'webm', 'ogg', 'mov', 'avi'])],
        help_text='Upload video file (MP4, WebM, OGG, MOV, AVI)'
    )
    
    video_url = models.URLField(
        blank=True,
        null=True,
        help_text='Or provide YouTube/Vimeo URL (e.g., https://www.youtube.com/watch?v=xxxxx)'
    )
    
    video_thumbnail = models.ImageField(
        upload_to='video_thumbnails/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text='Custom thumbnail for video (optional, will use featured_image if not provided)'
    )
    
    video_duration = models.DurationField(
        blank=True,
        null=True,
        help_text='Video duration (automatically calculated for uploaded videos)'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Draft")
    is_featured = models.BooleanField(default=False)
    is_editors_pick = models.BooleanField(default=False)
    tags = TaggableManager()
    views = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optional news-specific fields
    is_breaking_news = models.BooleanField(default=False, help_text="Mark as breaking news")
    news_priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('breaking', 'Breaking')
        ],
        default='medium',
        help_text="News priority level"
    )
    news_genre = models.CharField(
        max_length=100,
        blank=True,
        help_text="News genre (e.g., PressRelease, Satire, Blog, Opinion)"
    )
    exclude_from_news = models.BooleanField(
        default=False,
        help_text="Exclude from Google News sitemap"
    )
    # Additional news fields
    news_keywords = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated keywords for Google News"
    )
    
    geo_locations = models.CharField(
        max_length=255,
        blank=True,
        help_text="Geographic locations relevant to this story (comma-separated)"
    )

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Auto-generate alt text if not provided
        if not self.image_alt_text and self.featured_image:
            self.image_alt_text = f"Featured image for {self.title}"
        
        # NEW: Auto-set content_type based on video presence
        if self.video_file or self.video_url:
            # If has substantial text content, it's mixed
            from django.utils.html import strip_tags
            text_length = len(strip_tags(self.blog_body)) if self.blog_body else 0
            if text_length > 100:
                self.content_type = 'mixed'
            else:
                self.content_type = 'video'
        else:
            self.content_type = 'article'
            
        super().save(*args, **kwargs)

    @property
    def featured_image_base_name(self):
        """Base name without extension for responsive image generation."""
        if not self.featured_image:
            return ""
        return os.path.splitext(os.path.basename(self.featured_image.name))[0]

    @property
    def featured_image_dir(self):
        """Directory URL where the image is stored."""
        if not self.featured_image:
            return ""
        return os.path.dirname(self.featured_image.url)

    @property
    def featured_image_ext(self):
        """File extension in lowercase, including the dot."""
        if not self.featured_image:
            return ""
        return os.path.splitext(self.featured_image.name)[1].lower()
    
    # NEW: Video helper properties
    @property
    def is_video_post(self):
        """Check if this post has video content"""
        return self.content_type in ['video', 'mixed']
    
    @property
    def has_uploaded_video(self):
        """Check if post has uploaded video file"""
        return bool(self.video_file)
    
    @property
    def has_embedded_video(self):
        """Check if post has embedded video URL"""
        return bool(self.video_url)
    
    @property
    def video_thumbnail_url(self):
        """Get video thumbnail - custom or featured image"""
        if self.video_thumbnail:
            return self.video_thumbnail.url
        elif self.featured_image:
            return self.featured_image.url
        return None
    
    def get_video_embed_code(self):
        """
        Convert YouTube/Vimeo URL to embed format
        Matches YouTube's official embed code format
        """
        if not self.video_url:
            return ''
        
        import re
        url = self.video_url.strip()
        
        # YouTube: Extract 11-character video ID
        # Handles: youtube.com/watch?v=, youtu.be/, youtube.com/embed/
        youtube_match = re.search(
            r'(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})', 
            url
        )
        if youtube_match:
            video_id = youtube_match.group(1)
            return f'https://www.youtube.com/embed/{video_id}'
        
        # Vimeo: Extract numeric ID
        vimeo_match = re.search(r'vimeo\.com\/(\d+)', url)
        if vimeo_match:
            video_id = vimeo_match.group(1)
            return f'https://player.vimeo.com/video/{video_id}'
        
        # Fallback: return original URL
        return url
      
    @property
    def video_type_display(self):
        """Get display name for video type"""
        if self.has_uploaded_video:
            return 'Uploaded Video'
        elif self.has_embedded_video:
            if 'youtube' in self.video_url.lower():
                return 'YouTube Video'
            elif 'vimeo' in self.video_url.lower():
                return 'Vimeo Video'
            return 'External Video'
        return None

    # SEO Methods
    def get_meta_title(self):
        return self.meta_title or self.title
    
    def get_meta_description(self):
        if self.meta_description:
            return self.meta_description
        # Auto-generate from short_description, stripping HTML
        from django.utils.html import strip_tags
        return strip_tags(self.short_description)[:160]
    
    def get_reading_time(self):
        """Calculate reading time based on word count"""
        from django.utils.html import strip_tags
        word_count = len(strip_tags(self.blog_body).split())
        return max(1, round(word_count / 200))  # 200 words per minute
    
    def get_word_count(self):
        """Get word count for SEO analysis"""
        from django.utils.html import strip_tags
        return len(strip_tags(self.blog_body).split())
    
    def get_seo_score(self):
        """Calculate basic SEO score"""
        score = 0
        max_score = 100
        
        # Title optimization (20 points)
        if self.meta_title and 30 <= len(self.meta_title) <= 60:
            score += 20
        elif self.title and 30 <= len(self.title) <= 60:
            score += 15
        
        # Meta description (20 points)
        if self.meta_description and 120 <= len(self.meta_description) <= 160:
            score += 20
        
        # Focus keyword in title (15 points)
        if self.focus_keyword and self.focus_keyword.lower() in self.title.lower():
            score += 15
        
        # Content length (15 points)
        word_count = self.get_word_count()
        if word_count >= 300:
            score += 15
        
        # Image alt text (10 points)
        if self.image_alt_text:
            score += 10
        
        # Tags (10 points)
        if self.tags.count() >= 3:
            score += 10
        
        # Category (10 points)
        if self.category:
            score += 10
        
        return min(score, max_score)
    
    def get_absolute_url(self):
        return reverse('blogs', kwargs={
            'category_slug': self.category.slug,
            'slug': self.slug
        })
    
    @property
    def comment_count(self):
        """Get total number of comments using generic relation"""
        from comments.models import Comment
        from django.contrib.contenttypes.models import ContentType
        
        content_type = ContentType.objects.get_for_model(self)
        return Comment.objects.filter(
            content_type=content_type,
            object_id=self.id
        ).count()

    def get_structured_data(self):
        """Generate JSON-LD structured data"""
        data = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": f"https://yourdomain.com{self.get_absolute_url()}"
            },
            "headline": self.get_meta_title(),
            "description": self.get_meta_description(),
            "image": {
                "@type": "ImageObject",
                "url": self.featured_image.url if self.featured_image else "",
                "width": self.image_width,
                "height": self.image_height
            },
            "author": {
                "@type": "Person",
                "name": self.author.get_full_name() or self.author.username
            },
            "publisher": {
                "@type": "Organization",
                "name": "Your Blog Name",
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://yourdomain.com/static/logo.png"
                }
            },
            "datePublished": self.created_at.isoformat(),
            "dateModified": self.updated_at.isoformat(),
            "wordCount": self.get_word_count(),
            "timeRequired": f"PT{self.get_reading_time()}M",
            "keywords": [tag.name for tag in self.tags.all()],
            "articleSection": self.category.category_name,
            "url": f"https://yourdomain.com{self.get_absolute_url()}"
        }
        
        # NEW: Add video object to structured data if video exists
        if self.is_video_post:
            if self.has_uploaded_video:
                data["video"] = {
                    "@type": "VideoObject",
                    "name": self.title,
                    "description": self.get_meta_description(),
                    "thumbnailUrl": self.video_thumbnail_url,
                    "uploadDate": self.created_at.isoformat(),
                    "contentUrl": self.video_file.url if self.video_file else None,
                }
                if self.video_duration:
                    data["video"]["duration"] = f"PT{int(self.video_duration.total_seconds())}S"
            elif self.has_embedded_video:
                data["video"] = {
                    "@type": "VideoObject",
                    "name": self.title,
                    "description": self.get_meta_description(),
                    "thumbnailUrl": self.video_thumbnail_url,
                    "embedUrl": self.get_video_embed_code(),
                    "uploadDate": self.created_at.isoformat(),
                }
        
        return data
    
    def __str__(self):
        return self.title
    
class SocialLink(models.Model):
    platform = models.CharField(max_length=50)
    link = models.URLField()

    def __str__(self):
        return self.platform

class SiteSetting(models.Model):
    social_links = models.ManyToManyField(SocialLink, blank=True)
    site_name = models.CharField(max_length=100, default="My Blog", help_text="Site name for SEO")
    site_logo = models.ImageField(upload_to='site/', blank=True, help_text="Logo for social sharing")
    meta_description = models.CharField(max_length=160, blank=True, help_text="Default site description")
    meta_keywords = models.CharField(max_length=255, blank=True, help_text="Default site keywords")
    meta_author = models.CharField(max_length=100, blank=True, help_text="Default author name")
    google_analytics_id = models.CharField(max_length=20, blank=True, help_text="Google Analytics tracking ID")
    google_search_console = models.TextField(blank=True, help_text="Google Search Console verification code")

    def __str__(self):
        return "Site Settings"
    
class ContentAnalysis(models.Model):
    post = models.OneToOneField(Blog, on_delete=models.CASCADE)
    analysis_data = models.JSONField()
    overall_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LinkOpportunity(models.Model):
    """Model to store internal linking opportunities"""
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    anchor_text = models.CharField(max_length=255)
    target_url = models.URLField()
    target_post = models.ForeignKey('blogs.Blog', on_delete=models.CASCADE, null=True, blank=True)
    context = models.TextField()  # Surrounding text
    
    relevance_score = models.FloatField(default=0.0)
    implemented = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('content_type', 'object_id', 'anchor_text', 'target_url')

class BrokenLink(models.Model):
    """Model to track broken links"""
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    url = models.URLField()
    anchor_text = models.CharField(max_length=255)
    status_code = models.IntegerField()
    error_message = models.TextField(blank=True)
    
    first_detected = models.DateTimeField(auto_now_add=True)
    last_checked = models.DateTimeField(auto_now=True)
    fixed = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('content_type', 'object_id', 'url')

class LinkPerformance(models.Model):
    """Track link performance metrics"""
    link_url = models.URLField()
    source_post = models.ForeignKey('blogs.Blog', on_delete=models.CASCADE)
    
    clicks = models.IntegerField(default=0)
    impressions = models.IntegerField(default=0)
    ctr = models.FloatField(default=0.0)
    
    date = models.DateField(auto_now_add=True)
    
    class Meta:
        unique_together = ('link_url', 'source_post', 'date')
