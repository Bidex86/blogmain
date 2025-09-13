# accounts/urls.py
from django.urls import path
from .views import unsubscribe
from . import views
from .views import social_optin_view
from .views import CustomLoginView
from .views import CustomSignupView
from .views import toggle_theme
from .views import custom_logout_view

urlpatterns = [
    path('unsubscribe/', unsubscribe, name='unsubscribe'),
    path('social-optin/', social_optin_view, name='social_optin'),
    
    # Override allauth URLs
    path('accounts/login/', CustomLoginView.as_view(), name='account_login'),
    path("accounts/signup/", CustomSignupView.as_view(), name="account_signup"),
    path('accounts/logout/', custom_logout_view, name='account_logout'),  # Uncommented and fixed
    
    path("toggle-theme/", toggle_theme, name="toggle_theme"),
    path('accounts/settings/', views.profile_settings, name='profile_settings'),
    
]