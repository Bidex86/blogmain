# ads/context_processors.py
from django.conf import settings

def ad_settings(request):
    """Add advertisement settings to template context"""
    return {
        'ADS_ENABLED': hasattr(settings, 'ADS_SETTINGS'),
        'ADS_SETTINGS': getattr(settings, 'ADS_SETTINGS', {}),
    }