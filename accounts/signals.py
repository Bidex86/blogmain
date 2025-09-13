# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from allauth.account.signals import user_logged_in, user_signed_up
from .models import Profile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update Profile instance when User is created or updated"""
    Profile.objects.get_or_create(user=instance)

@receiver(user_logged_in)
def create_user_profile_on_login(sender, request, user, **kwargs):
    """Ensure profile exists when user logs in"""
    Profile.objects.get_or_create(user=user)

@receiver(user_signed_up)
def create_user_profile_on_signup(sender, request, user, **kwargs):
    """Ensure profile exists when user signs up"""
    Profile.objects.get_or_create(user=user)