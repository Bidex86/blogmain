# admin.py - Updated with video support (minimal changes to your existing file)

from django.contrib import admin
from django.forms import ModelForm
from django.utils.html import format_html
from .models import Blog, Category

# Custom form for better tags widget (UNCHANGED)
class BlogAdminForm(ModelForm):
    class Meta:
        model = Blog
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize the tags field widget
        if 'tags' in self.fields:
            self.fields['tags'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': 'Enter tags separated by commas (e.g., python, django, web)',
                'style': 'width: 100%; min-width: 400px;'
            })
            self.fields['tags'].help_text = (
                'Enter tags separated by commas. '
                'New tags will be created automatically.'
            )

# Main Blog admin class - UPDATED with video fields
class BlogAdmin(admin.ModelAdmin):
    form = BlogAdminForm
    
    # UPDATED: Add content_type to list_display
    list_display = [
        'title', 
        'content_type',  # NEW
        'category', 
        'author', 
        'status', 
        'is_breaking_news', 
        'news_priority', 
        'created_at', 
        'get_tags'
    ]
    
    # UPDATED: Add content_type to list_filter
    list_filter = [
        'status', 
        'content_type',  # NEW
        'category', 
        'is_featured', 
        'is_breaking_news', 
        'news_priority', 
        'created_at', 
        'tags'
    ]
    
    search_fields = ['title', 'blog_body', 'tags__name', 'news_keywords']
    prepopulated_fields = {'slug': ('title',)}
    list_per_page = 20
    
    # UPDATED: Add Video Content section to fieldsets
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'category', 'blog_body', 'short_description')
        }),
        ('Media', {
            'fields': ('featured_image', 'image_alt_text')
        }),
        ('Video Content (Optional)', {  # NEW SECTION
            'fields': ('video_file', 'video_url', 'video_thumbnail', 'video_duration'),
            'classes': ('collapse',),
            'description': 'Upload video file OR provide YouTube/Vimeo URL (not both). Content type is auto-detected.'
        }),
        ('SEO & Tags', {
            'fields': ('seo_keywords', 'tags', 'focus_keyword', 'meta_title', 'meta_description'),
            'description': 'Tags help categorize and make content discoverable.'
        }),
        ('News Settings', {
            'fields': ('is_breaking_news', 'news_priority', 'news_genre', 'news_keywords', 'geo_locations', 'exclude_from_news'),
            'classes': ('collapse',),
            'description': 'Configure Google News sitemap inclusion and metadata.'
        }),
        ('Publishing Options', {
            'fields': ('status', 'is_featured', 'is_editors_pick', 'author'),
            'classes': ('collapse',)
        }),
    )
    
    # Add custom admin actions (UNCHANGED)
    actions = [
        'mark_as_breaking_news', 
        'exclude_from_news_sitemap', 
        'include_in_news_sitemap',
        'duplicate_with_tags',
        'clear_all_tags'
    ]
    
    def mark_as_breaking_news(self, request, queryset):
        updated = queryset.update(is_breaking_news=True, news_priority='breaking')
        self.message_user(request, f'{updated} articles marked as breaking news.')
    mark_as_breaking_news.short_description = "Mark as breaking news"
    
    def exclude_from_news_sitemap(self, request, queryset):
        updated = queryset.update(exclude_from_news=True)
        self.message_user(request, f'{updated} articles excluded from news sitemap.')
    exclude_from_news_sitemap.short_description = "Exclude from news sitemap"
    
    def include_in_news_sitemap(self, request, queryset):
        updated = queryset.update(exclude_from_news=False)
        self.message_user(request, f'{updated} articles included in news sitemap.')
    include_in_news_sitemap.short_description = "Include in news sitemap"

    def get_tags(self, obj):
        """Display tags in list view"""
        tags = obj.tags.all()
        if not tags:
            return "No tags"
        tag_names = [tag.name for tag in tags[:3]]
        if tags.count() > 3:
            tag_names.append(f"... +{tags.count() - 3} more")
        return ", ".join(tag_names)
    get_tags.short_description = 'Tags'

    def duplicate_with_tags(self, request, queryset):
        """Custom action to duplicate posts with their tags"""
        for blog in queryset:
            old_tags = list(blog.tags.all())
            blog.pk = None
            blog.title = f"Copy of {blog.title}"
            blog.slug = None  # Will be auto-generated
            blog.save()
            blog.tags.set(old_tags)
        self.message_user(request, f"Successfully duplicated {queryset.count()} blog posts with tags.")
    duplicate_with_tags.short_description = "Duplicate selected blogs with tags"

    def clear_all_tags(self, request, queryset):
        """Remove all tags from selected posts"""
        for blog in queryset:
            blog.tags.clear()
        self.message_user(request, f"Cleared tags from {queryset.count()} blog posts.")
    clear_all_tags.short_description = "Clear all tags from selected blogs"

# Category admin (UNCHANGED)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['category_name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('category_name',)}
    search_fields = ['category_name']

# Register models
admin.site.register(Blog, BlogAdmin)
admin.site.register(Category, CategoryAdmin)

# Note: Tag model is automatically registered by django-taggit
# Don't try to register it manually unless you really need custom functionality
