# accounts/views.py
from django.shortcuts import redirect, render
from allauth.socialaccount.adapter import get_adapter
from allauth.account.utils import complete_signup
from allauth.socialaccount.models import SocialLogin
from django.contrib.auth.decorators import login_required
from allauth.socialaccount import signals
from allauth.utils import get_request_param
from .forms import SocialSignupForm
from .forms import NewsletterOptInForm
from allauth.account.views import SignupView
from .forms import CustomSignupForm
from django.contrib import messages
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount import providers
from allauth.account.views import LoginView
#from allauth.socialaccount.providers.google.views import oauth2_login
from django.views import View

#google_login_direct = oauth2_login

class CustomSignupView(SignupView):
    template_name = 'account/signup.html'
    form_class = CustomSignupForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        provider_map = {provider.id: provider for provider in providers.registry.get_list()}
        context['socialaccount_providers'] = provider_map
        return context


def toggle_theme(request):
    theme = request.GET.get("theme", "light")
    response = redirect(request.META.get("HTTP_REFERER", "/"))
    response.set_cookie("theme", theme, max_age=60 * 60 * 24 * 365)  # 1 year
    return response



from allauth.socialaccount import providers

class CustomLoginView(LoginView):
    template_name = 'account/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['socialaccount_providers'] = {
            provider.id: provider
            for provider in providers.registry.get_list()
        }
        return context

    
def social_newsletter_optin(request):
    try:
        sociallogin = SocialLogin.deserialize(request.session.get('socialaccount_sociallogin'))
    except Exception:
        sociallogin = None

    if not sociallogin:
        return redirect("account_signup")

    if request.method == 'POST':
        form = SocialSignupForm(request.POST)
        if form.is_valid():
            user = sociallogin.user
            user.save()

            # Ensure the profile exists and save the newsletter opt-in
            if hasattr(user, 'profile'):
                user.profile.newsletter_opt_in = form.cleaned_data['newsletter_opt_in']
                user.profile.save()

            # Properly complete the signup using allauth’s complete_signup
            return complete_signup(
                request,
                user,
                get_adapter(request).get_login_redirect_url(request),
                sociallogin.get_redirect_url(request),
            )
    else:
        form = SocialSignupForm()

    return render(request, "account/social_optin.html", {"form": form})

@login_required
def social_optin_view(request):
    user = request.user

    if request.method == "POST":
        form = NewsletterOptInForm(request.POST)
        if form.is_valid():
            newsletter_opt_in = form.cleaned_data.get("newsletter_opt_in", False)

            if hasattr(user, 'profile'):
                user.profile.newsletter_opt_in = newsletter_opt_in
                user.profile.save()
            return redirect('dashboard')  # or your desired redirect
    else:
        form = NewsletterOptInForm()

    return render(request, 'accounts/social_optin.html', {'form': form})

@login_required
def unsubscribe(request):
    if hasattr(request.user, 'profile'):
        request.user.profile.newsletter_opt_in = False
        request.user.profile.save()
    return redirect('account_logout')  # or redirect to a "Goodbye" page

def custom_logout_view(request):
    messages.success(request, "You have signed out.")
