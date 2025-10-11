"""
URL configuration for blogmain project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
Fixed URL configuration for blogmain project.
"""
from django.contrib import admin
from django.urls import include, path
from .import views
from django.conf.urls.static import static
from django.conf import settings
from blogs import views as BlogsView
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from blogs.sitemaps import BlogSitemap, CategorySitemap, StaticViewSitemap
from pages import views as pages_views
from . import views as main_views

from notifications import views as notification_views  # ADD THIS

sitemaps = {
    'blogs': BlogSitemap,
    'categories': CategorySitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Core views
    path('', views.home, name='home'),
    
    # Apps - Order matters for URL resolution
    path('comments/', include('comments.urls')),
    path('pages/', include('pages.urls')),
    path('dashboard/', include('dashboards.urls')),
    
    # Authentication - Must come before catch-all patterns
    path('accounts/', include('allauth.urls')),
    path('', include("accounts.urls")),  # Custom account views
    
    # CKEditor
    path("ckeditor5/", include('django_ckeditor_5.urls')),
    path('ads/', include('ads.urls')),  # Add this line
    
    # Blog URLs
    path('', include('blogs.urls')),  # This includes category and tag URLs
    
    # Search (specific route before catch-all)
    path('search/', BlogsView.search, name='search'),
    
    # New API endpoints for advanced features
    #path('api/analytics/', include('blogs.analytics_urls')),
    #path('api/ai-content/', include('blogs.ai_content_urls')),
    #path('api/voice-search/', include('blogs.voice_search_urls')),
    #path('api/link-building/', include('blogs.link_building_urls')),

    # ADD THESE TWO LINES:
    # Notification URLs
    path('notifications/subscribe/', notification_views.subscribe, name='push_subscribe'),
    path('notifications/unsubscribe/', notification_views.unsubscribe, name='push_unsubscribe'),
    path('notifications/list/', notification_views.notification_list, name='notification_list'),
    path('notifications/<int:notification_id>/mark-read/', notification_views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', notification_views.mark_all_read, name='mark_all_read'),
    path('notifications/preferences/', notification_views.notification_preferences, name='notification_preferences'),
    path('notifications/history/', notification_views.notification_history, name='notification_history'),
    
    # PWA endpoints
    path('manifest.json', main_views.manifest, name='manifest'),
    path('sw.js', main_views.service_worker, name='service_worker'),
    path('offline/', main_views.offline_page, name='offline'),
    
    # Sitemaps
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', main_views.robots_txt, name='robots_txt'),
    
    # Catch-all blog detail view (MUST be last)
    path('<slug:category_slug>/<slug:slug>/', BlogsView.blogs, name='blogs'),  
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)