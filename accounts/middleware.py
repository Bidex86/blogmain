from django.utils.cache import patch_cache_control
from django.urls import resolve

class AuthAwareCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Debug logging
        print(f"MIDDLEWARE - Method: {request.method}")
        print(f"MIDDLEWARE - Path: {request.path}")
        print(f"MIDDLEWARE - User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
        print(f"MIDDLEWARE - Authenticated: {request.user.is_authenticated}")
        
        # Only apply cache control to GET requests for authenticated users
        # Don't interfere with POST requests (forms, AJAX, etc.)
        if request.user.is_authenticated and request.method == 'GET':
            try:
                url_name = resolve(request.path_info).url_name
                print(f"MIDDLEWARE - URL name: {url_name}")
                
                # Define which pages should not be cached for authenticated users
                no_cache_views = [
                    'blogs',           # Blog detail pages
                    'home',            # Home page
                    'category_posts',  # Category pages
                    'search',          # Search results
                    'tagged_posts',    # Tagged posts
                ]
                
                if url_name in no_cache_views:
                    patch_cache_control(response, no_cache=True, no_store=True, must_revalidate=True)
                    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    response['Pragma'] = 'no-cache'
                    response['Expires'] = '0'
                    print(f"MIDDLEWARE - Added no-cache headers for {url_name}")
                
            except Exception as e:
                print(f"MIDDLEWARE - Error resolving URL: {e}")
                # If we can't resolve the URL, still add no-cache for authenticated users on GET requests
                if not request.path.startswith('/admin/') and not request.path.startswith('/accounts/'):
                    patch_cache_control(response, no_cache=True, no_store=True, must_revalidate=True)
        
        return response