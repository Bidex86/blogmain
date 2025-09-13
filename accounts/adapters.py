# accounts/adapters.py - Simplified approach
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        # Import here to avoid circular imports
        from .models import Profile
        
        # Ensure profile exists and set newsletter subscription for social users
        profile, created = Profile.objects.get_or_create(user=user)
        profile.newsletter_opt_in = True
        profile.save()
        
        return user

    def get_signup_redirect_url(self, request):
        # Get the next URL if available
        next_url = request.GET.get('next') or request.POST.get('next')
        if next_url:
            return next_url
        
        # Default redirect for social signups
        return getattr(settings, 'LOGIN_REDIRECT_URL', '/')