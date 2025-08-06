from django.urls import path
from .views import unsubscribe
from . import views
from .views import social_newsletter_optin
from .views import social_optin_view
from .views import CustomLoginView
from .views import CustomSignupView
from .views import toggle_theme

#from .views import google_login_direct  

urlpatterns = [
    path('unsubscribe/', unsubscribe, name='unsubscribe'),
    path('accounts/social-optin/', social_newsletter_optin, name='social_optin'),
    path('social-optin/', social_optin_view, name='social_optin'),
    path('accounts/login/', CustomLoginView.as_view(), name='account_login'),
    path("accounts/signup/", CustomSignupView.as_view(), name="account_signup"),
    path("toggle-theme/", toggle_theme, name="toggle_theme"),
   
    #path("google/login/direct/", google_login_direct, name="google_login_direct"),

    
]