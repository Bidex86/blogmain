from django.db import models
from django.db import models
from django.utils import timezone
from django.core.validators import URLValidator
import uuid

# Create your models here.
class AdPosition(models.Model):
    """Define where ads can be placed"""
    POSITION_CHOICES = [
        ('header', 'Header Banner'),
        ('sidebar', 'Sidebar'),
        ('footer', 'Footer'),
        ('in_content', 'In Content'),
        ('between_posts', 'Between Posts'),
        ('popup', 'Popup Modal'),
        ('sticky', 'Sticky/Fixed Position'),
    ]
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    position_type = models.CharField(max_length=20, choices=POSITION_CHOICES)
    description = models.TextField(blank=True)
    width = models.PositiveIntegerField(help_text="Width in pixels")
    height = models.PositiveIntegerField(help_text="Height in pixels")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['position_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_position_type_display()})"

class Advertisement(models.Model):
    """Individual advertisement"""
    AD_TYPES = [
        ('image', 'Image Banner'),
        ('html', 'HTML/Rich Content'),
        ('video', 'Video'),
        ('script', 'Third-party Script (Google Ads, etc.)'),
    ]
    
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Normal'),
        (3, 'High'),
        (4, 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    ad_type = models.CharField(max_length=20, choices=AD_TYPES)
    position = models.ForeignKey(AdPosition, on_delete=models.CASCADE)
    
    # Content fields
    image = models.ImageField(upload_to='ads/images/', blank=True, null=True)
    html_content = models.TextField(blank=True, help_text="HTML content for rich ads")
    script_content = models.TextField(blank=True, help_text="JavaScript/Third-party code")
    
    # Link and tracking
    click_url = models.URLField(blank=True, help_text="Where the ad links to")
    alt_text = models.CharField(max_length=200, blank=True)
    
    # Scheduling
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)
    
    # Targeting
    show_on_homepage = models.BooleanField(default=True)
    show_on_blog_posts = models.BooleanField(default=True)
    show_on_categories = models.BooleanField(default=True)
    target_categories = models.ManyToManyField('blogs.Category', blank=True)
    
    # Settings
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    is_active = models.BooleanField(default=True)
    open_in_new_tab = models.BooleanField(default=True)
    
    # Analytics
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.position.name})"
    
    @property
    def click_through_rate(self):
        if self.impressions > 0:
            return (self.clicks / self.impressions) * 100
        return 0
    
    @property
    def is_expired(self):
        if self.end_date:
            return timezone.now() > self.end_date
        return False
    
    def increment_impressions(self):
        """Track ad view"""
        self.impressions += 1
        self.save(update_fields=['impressions'])
    
    def increment_clicks(self):
        """Track ad click"""
        self.clicks += 1
        self.save(update_fields=['clicks'])

class AdClick(models.Model):
    """Track individual ad clicks for analytics"""
    advertisement = models.ForeignKey(Advertisement, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    referer = models.URLField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']

class AdImpression(models.Model):
    """Track ad impressions"""
    advertisement = models.ForeignKey(Advertisement, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    page_url = models.URLField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']