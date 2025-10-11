from django.contrib import admin
from .models import PushSubscription, NotificationPreference, Notification

# Register your models here.


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'user__email']

@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'notify_new_posts', 'notify_comments', 'push_enabled', 'email_enabled']
    list_filter = ['notify_new_posts', 'notify_comments', 'push_enabled']
    search_fields = ['user__username']
    filter_horizontal = ['categories']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'title', 'is_read', 'is_sent', 'created_at']
    list_filter = ['type', 'is_read', 'is_sent', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at']