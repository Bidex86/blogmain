from django import forms
from .models import NotificationPreference
from blogs.models import Category

class NotificationPreferenceForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select categories you want to receive notifications for. Leave empty to receive all."
    )
    
    class Meta:
        model = NotificationPreference
        fields = [
            'notify_new_posts',
            'notify_comments',
            'notify_comment_replies',
            'notify_system',
            'categories',
            'push_enabled',
            'email_enabled',
        ]
        widgets = {
            'notify_new_posts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_comments': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_comment_replies': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'push_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'notify_new_posts': 'New blog posts',
            'notify_comments': 'New comments on posts I follow',
            'notify_comment_replies': 'Replies to my comments',
            'notify_system': 'System notifications',
            'push_enabled': 'Enable push notifications',
            'email_enabled': 'Enable email notifications',
        }