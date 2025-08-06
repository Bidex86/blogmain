
from django.contrib.admin.sites import AlreadyRegistered
from django.contrib import admin
from .models import Category, Blog, Comment, SocialLink

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('category_name',)}

class BlogAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'category', 'author', 'status', 'is_featured', 'is_editors_pick', 'views', 'created_at')
    search_fields = ('id', 'title', 'category__category_name', 'status')
    list_editable = ('is_featured', 'is_editors_pick',)


# Register your models here.
admin.site.register(Category, CategoryAdmin)
admin.site.register(Blog, BlogAdmin)
admin.site.register(Comment)
admin.site.register(SocialLink)