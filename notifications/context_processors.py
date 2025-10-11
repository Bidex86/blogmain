from django.conf import settings

def webpush_settings(request):
    return {
        'WEBPUSH_SETTINGS': settings.WEBPUSH_SETTINGS
    }