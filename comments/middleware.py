# comments/middleware.py - Complete corrected version
from django.http import HttpResponseBadRequest, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
import time
import logging

logger = logging.getLogger(__name__)


class CommentRateLimitMiddleware(MiddlewareMixin):
    """Prevent comment spam by rate limiting"""
    
    def process_request(self, request):
        # Only apply to comment add requests
        if not (request.path.startswith('/comments/add/') and request.method == 'POST'):
            return None
        
        try:
            # Skip rate limiting for staff users
            if request.user.is_authenticated and request.user.is_staff:
                return None
            
            user_id = request.user.id if request.user.is_authenticated else None
            ip_address = self.get_client_ip(request)
            
            # Create rate limit key
            rate_key = f"comment_rate:{user_id or ip_address}"
            
            # Check if user/IP has commented recently
            last_comment_time = cache.get(rate_key)
            if last_comment_time:
                time_diff = time.time() - last_comment_time
                min_interval = 30  # 30 seconds between comments
                
                if time_diff < min_interval:
                    wait_time = int(min_interval - time_diff)
                    error_msg = f"Please wait {wait_time} seconds before posting another comment."
                    
                    # Return JSON for AJAX requests
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': error_msg
                        }, status=429)
                    
                    return HttpResponseBadRequest(error_msg)
            
            # Set new timestamp (cache for 2 minutes)
            cache.set(rate_key, time.time(), 120)
            
            return None
        
        except Exception as e:
            # Don't block requests if rate limiting fails
            logger.error(f"Rate limiting error: {e}")
            return None
    
    def get_client_ip(self, request):
        """Get the client's IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or 'unknown'