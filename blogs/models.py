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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.category_name)
        super().save(*args, **kwargs)    


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
    seo_keywords = models.CharField(max_length=255, blank=True, help_text="Comma-separated keywords for auto-linking")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    featured_image = models.ImageField(upload_to='uploads/%Y/%m/%d', validators=[validate_image_extension])
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

    
    def get_absolute_url(self):
        return reverse('blogs', kwargs={
            'category_slug': self.category.slug,
            'slug': self.slug
        })
    
    def __str__(self):
        return self.title
    
class SocialLink(models.Model):
    platform = models.CharField(max_length=50)
    link = models.URLField()

    def __str__(self):
        return self.platform

class SiteSetting(models.Model):
    social_links = models.ManyToManyField(SocialLink, blank=True)
    meta_description = models.CharField(max_length=255, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    meta_author = models.CharField(max_length=100, blank=True)


    def __str__(self):
        return "Site Settings"
    

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    comment = models.TextField(max_length=250)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username}: {self.comment[:30]}'


