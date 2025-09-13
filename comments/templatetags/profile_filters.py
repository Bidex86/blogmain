# Create a new file: comments/templatetags/profile_filters.py
from django import template

register = template.Library()

@register.filter
def get_avatar_url(user):
    """Safely get user avatar URL"""
    try:
        if hasattr(user, 'profile') and user.profile:
            if hasattr(user.profile, 'avatar') and user.profile.avatar:
                return user.profile.avatar.url
    except:
        pass
    return '/static/images/default-avatar.png'

@register.filter
def has_profile(user):
    """Check if user has a profile"""
    try:
        return hasattr(user, 'profile') and user.profile is not None
    except:
        return False

@register.filter
def get_profile_attr(user, attr_name):
    """Safely get profile attribute"""
    try:
        if hasattr(user, 'profile') and user.profile:
            return getattr(user.profile, attr_name, None)
    except:
        pass
    return None