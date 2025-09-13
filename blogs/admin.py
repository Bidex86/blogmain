# admin.py - Clean version without repetitions

from django.contrib import admin
from django.forms import ModelForm
from .models import Blog, Category

# Custom form for better tags widget
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

# Main Blog admin class
class BlogAdmin(admin.ModelAdmin):
    form = BlogAdminForm
    list_display = ['title', 'category', 'author', 'status', 'created_at', 'get_tags']
    list_filter = ['status', 'category', 'is_featured', 'created_at', 'tags']
    search_fields = ['title', 'blog_body', 'tags__name']
    prepopulated_fields = {'slug': ('title',)}
    list_per_page = 20
    
    # Custom fieldsets for better organization
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'category', 'blog_body', 'short_description')
        }),
        ('Media', {
            'fields': ('featured_image',)
        }),
        ('SEO & Tags', {
            'fields': ('seo_keywords', 'tags'),
            'description': 'Tags help categorize and make content discoverable.'
        }),
        ('Publishing Options', {
            'fields': ('status', 'is_featured', 'is_editors_pick', 'author'),
            'classes': ('collapse',)
        }),
    )
    
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
    
    # Custom actions
    actions = ['duplicate_with_tags', 'clear_all_tags']
    
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

# Category admin
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['category_name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('category_name',)}
    search_fields = ['category_name']

# Register models
admin.site.register(Blog, BlogAdmin)
admin.site.register(Category, CategoryAdmin)

# Note: Tag model is automatically registered by django-taggit
# Don't try to register it manually unless you really need custom functionality