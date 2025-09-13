# accounts/views.py
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from .forms import NewsletterOptInForm
from allauth.account.views import SignupView, LoginView
from .forms import CustomSignupForm, ProfileForm
from django.contrib import messages
from django.contrib.auth.models import User
from allauth.socialaccount import providers
from django.views import View
from .models import Profile
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings



@login_required(login_url='/accounts/login/')
def profile_settings(request):
    """View for user to edit their profile settings"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile_settings')
    else:
        form = ProfileForm(instance=profile)
    
    return render(request, 'account/profile_settings.html', {
        'form': form,
        'profile': profile
    })


class CustomSignupView(SignupView):
    template_name = 'account/signup.html'
    form_class = CustomSignupForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provider_map = {provider.id: provider for provider in providers.registry.get_list()}
        context['socialaccount_providers'] = provider_map
        return context

    def form_valid(self, form):
        """Override to ensure profile is created immediately"""
        response = super().form_valid(form)
        # Force profile creation
        if self.user and not hasattr(self.user, 'profile'):
            Profile.objects.get_or_create(user=self.user)
        return response

    def get_success_url(self):
        """Override to redirect properly after signup"""
        # Get the next URL from the request or default to home
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url:
            return next_url
        return getattr(settings, 'LOGIN_REDIRECT_URL', '/')


class CustomLoginView(LoginView):
    template_name = 'account/login.html'

    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['socialaccount_providers'] = {
            provider.id: provider
            for provider in providers.registry.get_list()
        }
        return context

    def get_success_url(self):
        """Override to handle redirect properly after login"""
        # Get the next URL from the request
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url and next_url != self.request.path:
            return next_url
        
        # Default redirect based on user type
        if self.request.user.is_staff or self.request.user.is_superuser:
            return getattr(settings, 'LOGIN_REDIRECT_URL', '/dashboard/')
        
        return getattr(settings, 'LOGIN_REDIRECT_URL', '/')


def toggle_theme(request):
    theme = request.GET.get("theme", "light")
    response = redirect(request.META.get("HTTP_REFERER", "/"))
    response.set_cookie("theme", theme, max_age=60 * 60 * 24 * 365)  # 1 year
    return response


@login_required(login_url='/accounts/login/')
def social_optin_view(request):
    user = request.user

    if request.method == "POST":
        form = NewsletterOptInForm(request.POST)
        if form.is_valid():
            newsletter_opt_in = form.cleaned_data.get("newsletter_opt_in", False)

            profile, created = Profile.objects.get_or_create(user=user)
            profile.newsletter_opt_in = newsletter_opt_in
            profile.save()
                
            # Add success message
            if newsletter_opt_in:
                messages.success(request, "You have successfully subscribed to our newsletter!")
            else:
                messages.success(request, "You have been unsubscribed from our newsletter.")
                
            return redirect('dashboard')  # or your desired redirect
    else:
        # Initialize form with current user's newsletter preference
        profile, created = Profile.objects.get_or_create(user=user)
        form = NewsletterOptInForm(initial={'newsletter_opt_in': profile.newsletter_opt_in})

    return render(request, 'accounts/newsletter_settings.html', {'form': form})


@login_required(login_url='/accounts/login/')
def unsubscribe(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    profile.newsletter_opt_in = False
    profile.save()
    messages.success(request, "You have been successfully unsubscribed from our newsletter.")
    return render(request, 'accounts/unsubscribe.html')


def custom_logout_view(request):
    """Custom logout view with proper message handling"""
    if request.method == 'POST':
        logout(request)
        messages.success(request, "You have signed out successfully.")
        return redirect('/')
    
    # If GET request, show confirmation page
    return render(request, 'account/logout.html')