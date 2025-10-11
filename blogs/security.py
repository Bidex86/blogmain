# blogs/security.py
from django.conf import settings
from django.middleware.security import SecurityMiddleware
from django.http import HttpResponse
from django.utils.cache import add_never_cache_headers
from django.core.cache import cache
import hashlib
import time
from PIL import Image
import os

class SecurityHardeningMiddleware:
    """Advanced security hardening middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        self.add_security_headers(response)
        
        # Add CSP header
        self.add_csp_header(response)
        
        return response
    
    def add_security_headers(self, response):
        """Add comprehensive security headers"""
        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        }
        
        for header, value in security_headers.items():
            if header not in response:
                response[header] = value
    
    def add_csp_header(self, response):
        """Add Content Security Policy header"""
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://www.google-analytics.com https://cdnjs.cloudflare.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self' https://www.google-analytics.com",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        
        response['Content-Security-Policy'] = '; '.join(csp_directives)

class RateLimitingMiddleware:
    """Rate limiting middleware to prevent abuse"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = {
            'api': {'requests': 100, 'window': 3600},  # 100 requests per hour
            'comments': {'requests': 10, 'window': 600},  # 10 comments per 10 minutes
            'search': {'requests': 50, 'window': 3600},  # 50 searches per hour
        }
    
    def __call__(self, request):
        # Check rate limits
        if self.is_rate_limited(request):
            return HttpResponse(
                'Rate limit exceeded. Please try again later.',
                status=429,
                headers={'Retry-After': '3600'}
            )