from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import AdPosition, Advertisement, AdClick, AdImpression

# Register your models here.
# ads/admin.py

@admin.register(AdPosition)
class AdPositionAdmin(admin.ModelAdmin):
    list_display = ['name', 'position_type', 'width', 'height', 'is_active', 'created_at']
    list_filter = ['position_type', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Advertisement)
class AdvertisementAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'position', 'ad_type', 'is_active', 
        'impressions', 'clicks', 'ctr', 'priority', 
        'start_date', 'end_date', 'preview'
    ]
    list_filter = [
        'ad_type', 'is_active', 'priority', 'position__position_type',
        'show_on_homepage', 'show_on_blog_posts', 'show_on_categories'
    ]
    search_fields = ['title', 'html_content']
    readonly_fields = ['impressions', 'clicks', 'ctr', 'id', 'created_at', 'updated_at']
    filter_horizontal = ['target_categories']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'ad_type', 'position', 'priority', 'is_active')
        }),
        ('Content', {
            'fields': ('image', 'html_content', 'script_content', 'click_url', 'alt_text', 'open_in_new_tab')
        }),
        ('Scheduling', {
            'fields': ('start_date', 'end_date')
        }),
        ('Targeting', {
            'fields': ('show_on_homepage', 'show_on_blog_posts', 'show_on_categories', 'target_categories'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('impressions', 'clicks', 'ctr'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def ctr(self, obj):
        return f"{obj.click_through_rate:.2f}%"
    ctr.short_description = "CTR"
    
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:100px; max-height:50px;" />',
                obj.image.url
            )
        elif obj.ad_type == 'html':
            return format_html(
                '<div style="max-width:200px; overflow:hidden;">{}</div>',
                obj.html_content[:100] + '...' if len(obj.html_content) > 100 else obj.html_content
            )
        return "No preview"
    preview.short_description = "Preview"
    
    actions = ['activate_ads', 'deactivate_ads']
    
    def activate_ads(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} ads activated.')
    activate_ads.short_description = "Activate selected ads"
    
    def deactivate_ads(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} ads deactivated.')
    deactivate_ads.short_description = "Deactivate selected ads"

@admin.register(AdClick)
class AdClickAdmin(admin.ModelAdmin):
    list_display = ['advertisement', 'ip_address', 'user', 'timestamp']
    list_filter = ['timestamp', 'advertisement__position']
    search_fields = ['advertisement__title', 'ip_address']
    readonly_fields = ['advertisement', 'ip_address', 'user_agent', 'referer', 'timestamp', 'user']
    
    def has_add_permission(self, request):
        return False

@admin.register(AdImpression)
class AdImpressionAdmin(admin.ModelAdmin):
    list_display = ['advertisement', 'ip_address', 'user', 'page_url', 'timestamp']
    list_filter = ['timestamp', 'advertisement__position']
    search_fields = ['advertisement__title', 'ip_address', 'page_url']
    readonly_fields = ['advertisement', 'ip_address', 'page_url', 'timestamp', 'user']
    
    def has_add_permission(self, request):
        return False