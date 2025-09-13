# comments/apps.py
from django.apps import AppConfig
from django.conf import settings

class CommentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'comments'
    
    def ready(self):
        # Import signals
        import comments.signals
        
        # Set default comment settings
        if not hasattr(settings, 'COMMENTS_SETTINGS'):
            settings.COMMENTS_SETTINGS = {
                'MAX_DEPTH': 4,
                'MAX_LENGTH': 1000,
                'ALLOW_ANONYMOUS': False,
                'MODERATION_REQUIRED': False,
                'ALLOW_EDITING': True,
                'EDIT_TIME_LIMIT': 15,  # minutes
                'PAGINATION_SIZE': 10,
                'ENABLE_LIKES': True,
                'ENABLE_FLAGS': True,
                'AUTO_APPROVE': True,
            }