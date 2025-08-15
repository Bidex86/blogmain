
from django import forms
from blogs.models import Blog, Category
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django_ckeditor_5.widgets import CKEditor5Widget


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_name']

class BlogPostForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ('title', 'category', 'seo_keywords', 'featured_image', 'short_description', 'blog_body', 'status', 'is_featured', 'is_editors_pick', 'tags')
        widgets = {
            'tags': forms.TextInput(attrs={
                'class': 'tag-input',
                'placeholder': 'Enter tags separated by commas...',
            }),
        }

class AddUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')

class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
