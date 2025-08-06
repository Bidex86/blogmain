from django.contrib import admin
from .models import Profile



class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'newsletter_opt_in')
    list_filter = ('newsletter_opt_in',)
    search_fields = ('user__username', 'user__email')

# Register your models here.
admin.site.register(Profile)
