# ads/urls.py
from django.urls import path
from . import views

app_name = 'ads'

urlpatterns = [
    # Tracking URLs
    path('track-impression/<uuid:ad_id>/', views.track_impression, name='track_impression'),
    path('track-click/<uuid:ad_id>/', views.track_click, name='track_click'),
    path('track-impression-ajax/', views.ad_ajax_impression, name='ajax_impression'),
    
    # Analytics
    path('analytics/', views.ad_analytics, name='analytics'),
]

# Add to main urls.py:
# path('ads/', include('ads.urls')),