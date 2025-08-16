from django import forms
from .models import Page
from django_ckeditor_5.fields import CKEditor5Field


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ["title", "content", "status"]
