from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from django.urls import reverse
from taggit.managers import TaggableManager
from django.core.exceptions import ValidationError
import os




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

def validate_image_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png']
    if ext not in valid_extensions:
        raise ValidationError('Only .jpg, .jpeg, .png images are allowed')

class Blog(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    
    # SEO Enhancement Fields
    meta_title = models.CharField(max_length=60, blank=True, help_text="SEO title (60 chars max)")
    meta_description = models.TextField(max_length=160, blank=True, help_text="SEO description (160 chars max)")
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Draft")
    is_featured = models.BooleanField(default=False)
    is_editors_pick = models.BooleanField(default=False)
    tags = TaggableManager()  # Add this line
    views = models.IntegerField(default=0)  # Needed for trending logic
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Auto-generate alt text if not provided
        if not self.image_alt_text and self.featured_image:
            self.image_alt_text = f"Featured image for {self.title}"
            
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
        return {
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
    

#class Comment(models.Model):
    #user = models.ForeignKey(User, on_delete=models.CASCADE)
    #blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    #comment = models.TextField(max_length=250)
    #parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    #created_at = models.DateTimeField(auto_now_add=True)
    #updated_at = models.DateTimeField(auto_now=True)

    #def __str__(self):
        #return f'{self.user.username}: {self.comment[:30]}'