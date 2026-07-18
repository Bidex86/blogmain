from django import forms
from blogs.models import Blog, Category
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django_ckeditor_5.widgets import CKEditor5Widget


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_name', 'parent']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Category.objects.filter(parent__isnull=True).order_by('category_name')
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)          # not its own parent
            qs = qs.exclude(children__isnull=False)        # don't nest under a category that has kids
        self.fields['parent'].queryset = qs.distinct()
        self.fields['parent'].required = False
        self.fields['parent'].empty_label = "— None (top-level category) —"
        
class BlogPostForm(forms.ModelForm):
    class Meta:
        model = Blog
        # FIXED: Removed 'content_type' - it's auto-detected by the model!
        fields = (
            'title', 
            'category', 
            'seo_keywords', 
            'focus_keyword', 
            'meta_title', 
            'meta_description', 
            'featured_image', 
            'short_description', 
            'blog_body', 
            # Video fields (content_type is AUTO-DETECTED, not in form)
            'video_file',
            'video_url', 
            'video_thumbnail',
            'video_duration',
            # Existing fields
            'status', 
            'is_featured', 
            'is_editors_pick', 
            'tags'
        )
        
        widgets = {
            'tags': forms.TextInput(attrs={
                'class': 'tag-input',
                'placeholder': 'Enter tags separated by commas...',
            }),
            # Custom widgets for video fields
            'video_file': forms.FileInput(attrs={
                'class': 'video-file-input',
                'accept': 'video/mp4,video/webm,video/ogg,video/mov,video/avi',
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'video-url-input',
                'placeholder': 'https://www.youtube.com/watch?v=xxxxx or https://vimeo.com/xxxxx',
            }),
            'video_thumbnail': forms.FileInput(attrs={
                'class': 'video-thumbnail-input',
                'accept': 'image/jpeg,image/jpg,image/png',
            }),
            'video_duration': forms.TimeInput(attrs={
                'class': 'video-duration-input',
                'placeholder': 'HH:MM:SS',
            }),
        }
        
        help_texts = {
            'video_file': 'Upload a video file OR provide a YouTube/Vimeo URL below (not both)',
            'video_url': 'Paste YouTube or Vimeo URL here if not uploading a file',
            'video_thumbnail': 'Optional: Custom thumbnail image for the video',
            'video_duration': 'Optional: Auto-calculated for uploaded videos, or enter manually',
        }
    
    def clean(self):
        """Validate that user doesn't upload video AND provide URL"""
        cleaned_data = super().clean()
        video_file = cleaned_data.get('video_file')
        video_url = cleaned_data.get('video_url')
        
        # Check if both video file and URL are provided
        if video_file and video_url:
            raise forms.ValidationError(
                "Please provide either a video file OR a video URL, not both."
            )
        
        return cleaned_data

class AddUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')

class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')