# comments/templatetags/profile_filters.py - Complete version
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

@register.filter
def user_initials(user):
    """Get user initials for avatar placeholder"""
    try:
        if user.first_name and user.last_name:
            return f"{user.first_name[0]}{user.last_name[0]}".upper()
        elif user.first_name:
            return user.first_name[0].upper()
        elif user.username:
            return user.username[0].upper()
    except:
        pass
    return "U"