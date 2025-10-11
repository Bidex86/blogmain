# API URLs - blogs/analytics_urls.py
from django.urls import path
from . import analytics_views

urlpatterns = [
    path('events/', analytics_views.track_events, name='track_events'),
    path('core-web-vitals/', analytics_views.track_core_web_vitals, name='track_core_web_vitals'),
    path('performance/', analytics_views.get_performance_metrics, name='get_performance_metrics'),
    path('content-insights/', analytics_views.get_content_insights, name='get_content_insights'),
]