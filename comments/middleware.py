# comments/middleware.py
from django.http import HttpResponseBadRequest
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
import time

class CommentRateLimitMiddleware(MiddlewareMixin):
    """Prevent comment spam by rate limiting"""
    
    def process_request(self, request):
        if request.path.startswith('/comments/add/') and request.method == 'POST':
            user_id = request.user.id if request.user.is_authenticated else None
            ip_address = self.get_client_ip(request)
            
            # Create rate limit key
            rate_key = f"comment_rate:{user_id or ip_address}"
            
            # Check if user/IP has commented recently
            last_comment_time = cache.get(rate_key)
            if last_comment_time:
                time_diff = time.time() - last_comment_time
                if time_diff < 30:  # 30 seconds between comments
                    return HttpResponseBadRequest("Please wait before posting another comment.")
            
            # Set new timestamp
            cache.set(rate_key, time.time(), 60)  # Cache for 1 minute
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip