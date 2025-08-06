from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import resolve_url


class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        newsletter_opt_in = request.POST.get("newsletter_opt_in") == "on"
        if hasattr(user, "profile"):
            user.profile.newsletter_opt_in = newsletter_opt_in
            user.profile.save()
        return user

    def get_signup_redirect_url(self, request):
        return resolve_url("social_newsletter_optin")
