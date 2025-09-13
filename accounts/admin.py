from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db.models import BooleanField, OuterRef, Subquery
from .models import Profile


# Inline profile (inside User detail page)
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Profile"


# --- Proxy model for User to expose profile field ---
class UserProxy(User):
    class Meta:
        proxy = True
        verbose_name = "User"
        verbose_name_plural = "Users"


# --- Custom UserAdmin ---
class UserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "newsletter_opt_in",
    )
    
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    inlines = [ProfileInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Annotate newsletter status from Profile into UserProxy
        profile_subquery = Profile.objects.filter(user=OuterRef("pk")).values("newsletter_opt_in")[:1]
        return qs.annotate(newsletter_opt_in=Subquery(profile_subquery, output_field=BooleanField()))

    def newsletter_opt_in(self, obj):
        return obj.newsletter_opt_in
    newsletter_opt_in.boolean = True
    newsletter_opt_in.admin_order_field = "newsletter_opt_in"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        profile, created = Profile.objects.get_or_create(user=obj)
        if "newsletter_opt_in" in form.cleaned_data:
            profile.newsletter_opt_in = form.cleaned_data["newsletter_opt_in"]
            profile.save()


# --- Register the proxy instead of default User ---
admin.site.unregister(User)
admin.site.register(UserProxy, UserAdmin)


# --- Hide Profile from sidebar ---
@admin.register(Profile)
class HiddenProfileAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return False