# accounts/forms.py
from allauth.account.forms import SignupForm
from allauth.account.forms import LoginForm
from django import forms

class CustomSignupForm(SignupForm):
    newsletter_opt_in = forms.BooleanField(
        label="Subscribe to our newsletter",
        required=False
    )

    def signup(self, request, user):
        user.save()
        # Ensure the profile exists before accessing it
        if hasattr(user, 'profile'):
            user.profile.newsletter_opt_in = self.cleaned_data.get('newsletter_opt_in')
            user.profile.save()
        return user
    
class CustomLoginForm(LoginForm):
    def login(self, *args, **kwargs):
        # Add any custom logic here
        return super().login(*args, **kwargs)
        
# accounts/forms.py
class SocialSignupForm(forms.Form):
    newsletter_opt_in = forms.BooleanField(
        label="Subscribe to our newsletter",
        required=False
    )

    
class NewsletterOptInForm(forms.Form):
    newsletter_opt_in = forms.BooleanField(
        label="Subscribe to our newsletter",
        required=False
    )
