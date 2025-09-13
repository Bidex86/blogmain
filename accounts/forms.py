# accounts/forms.py
from allauth.account.forms import SignupForm, LoginForm
from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):  # Changed from forms.Form to forms.ModelForm
    class Meta:
        model = Profile
        fields = ['avatar', 'newsletter_opt_in', 'email_on_reply', 'email_on_mention']
        widgets = {
            'avatar': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*'
            }),
            'newsletter_opt_in': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'email_on_reply': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'email_on_mention': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'newsletter_opt_in': 'Subscribe to our newsletter',
            'email_on_reply': 'Receive email when someone replies to your comment',
            'email_on_mention': 'Receive email when mentioned in a comment',
        }

class CustomSignupForm(SignupForm):
    newsletter_opt_in = forms.BooleanField(
        label="Subscribe to our newsletter",
        required=False,
        initial=True,  # This makes the checkbox checked by default
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def signup(self, request, user):
        user.save()
        # Ensure the profile exists before accessing it
        profile, created = Profile.objects.get_or_create(user=user)
        
        # If newsletter_opt_in is not in cleaned_data or is None, default to True
        newsletter_opt_in = self.cleaned_data.get('newsletter_opt_in', True)
        if newsletter_opt_in is None:
            newsletter_opt_in = True
            
        profile.newsletter_opt_in = newsletter_opt_in
        profile.save()
        return user
    
class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add custom styling or modifications if needed
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

    
    #def login(self, request, user):
        # Ensure profile exists on login
        #Profile.objects.get_or_create(user=user)
        #return super().login(request, user)

# Keep this form for account settings page        
class NewsletterOptInForm(forms.Form):
    newsletter_opt_in = forms.BooleanField(
        label="Subscribe to our newsletter",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )