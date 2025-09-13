# dashboards/middleware.py
from django.utils.cache import add_never_cache_headers

class AdminNoCacheMiddleware:
    """
    Middleware to disable caching for admin dashboard pages
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Disable caching for admin dashboard URLs
        if (request.path.startswith('/dashboard/') or 
            request.path.startswith('/admin/') or
            request.user.is_authenticated and request.user.is_staff):
            
            add_never_cache_headers(response)
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response