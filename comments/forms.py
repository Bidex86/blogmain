# comments/forms.py - Enhanced with better validation
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from .models import Comment, CommentFlag

class CommentForm(forms.ModelForm):
    """Enhanced comment form with validation and spam detection"""
    
    # Hidden fields for object identification
    content_type_id = forms.IntegerField(widget=forms.HiddenInput())
    object_id = forms.IntegerField(widget=forms.HiddenInput())
    parent_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)
    
    class Meta:
        model = Comment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control comment-textarea',
                'rows': 4,
                'placeholder': 'Share your thoughts...',
                'maxlength': getattr(settings, 'COMMENTS_MAX_LENGTH', 1000),
                'data-auto-resize': 'true',
            })
        }
    
    def __init__(self, *args, **kwargs):
        # Extract object information
        self.content_object = kwargs.pop('content_object', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pre-populate hidden fields if content_object provided
        if self.content_object:
            content_type = ContentType.objects.get_for_model(self.content_object)
            self.fields['content_type_id'].initial = content_type.id
            self.fields['object_id'].initial = self.content_object.pk
        
        # Add character counter attributes
        max_length = getattr(settings, 'COMMENTS_MAX_LENGTH', 1000)
        self.fields['comment'].widget.attrs['maxlength'] = max_length
    
    def clean_comment(self):
        """Enhanced comment validation"""
        comment = self.cleaned_data.get('comment')
        
        if not comment or not comment.strip():
            raise forms.ValidationError('Comment cannot be empty.')
        
        comment = comment.strip()
        
        # Check minimum length
        if len(comment) < 10:
            raise forms.ValidationError('Comment must be at least 10 characters long.')
        
        # Check maximum length
        max_length = getattr(settings, 'COMMENTS_MAX_LENGTH', 1000)
        if len(comment) > max_length:
            raise forms.ValidationError(f'Comment cannot exceed {max_length} characters.')
        
        # Check for spam (if user is authenticated)
        if self.user and self.user.is_authenticated:
            from .utils import detect_spam_content
            if detect_spam_content(comment):
                raise forms.ValidationError('Comment appears to contain spam content.')
        
        # Check for excessive repeated characters
        import re
        if re.search(r'(.)\1{10,}', comment):
            raise forms.ValidationError('Comment contains excessive repeated characters.')
        
        # Check for excessive caps
        if len(comment) > 50 and sum(1 for c in comment if c.isupper()) / len(comment) > 0.7:
            raise forms.ValidationError('Please avoid excessive use of capital letters.')
        
        return comment
    
    def clean(self):
        """Enhanced validation for the entire form"""
        cleaned_data = super().clean()
        
        # Validate object exists
        content_type_id = cleaned_data.get('content_type_id')
        object_id = cleaned_data.get('object_id')
        
        if content_type_id and object_id:
            try:
                content_type = ContentType.objects.get(id=content_type_id)
                content_object = content_type.get_object_for_this_type(id=object_id)
                cleaned_data['content_object'] = content_object
            except (ContentType.DoesNotExist, content_type.model_class().DoesNotExist):
                raise forms.ValidationError('Invalid object reference.')
        
        # Validate parent comment if replying
        parent_id = cleaned_data.get('parent_id')
        if parent_id:
            try:
                parent = Comment.objects.get(
                    id=parent_id,
                    content_type_id=content_type_id,
                    object_id=object_id
                )
                if parent.max_depth_reached:
                    raise forms.ValidationError('Cannot reply: maximum nesting depth reached.')
                cleaned_data['parent'] = parent
            except Comment.DoesNotExist:
                raise forms.ValidationError('Parent comment not found.')
        
        # Check if user is banned from commenting
        if self.user and hasattr(self.user, 'profile'):
            if self.user.profile.is_comment_banned:
                raise forms.ValidationError('You are temporarily banned from commenting.')
        
        return cleaned_data
    
    def _is_spam(self, text):
        """Basic spam detection"""
        spam_patterns = [
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+])+',  # URLs
            r'(.)\1{4,}',  # Repeated characters (5 or more)
            r'\b(viagra|casino|lottery|winner|prize|click here|buy now)\b',  # Spam keywords
        ]
        
        import re
        spam_score = 0
        
        for pattern in spam_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                spam_score += 1
        
        return spam_score >= 2  # Adjust threshold as needed
    
    def _has_excessive_caps(self, text):
        """Check for excessive capital letters"""
        if len(text) < 10:  # Skip short comments
            return False
        
        caps_count = sum(1 for c in text if c.isupper())
        caps_ratio = caps_count / len(text)
        
        return caps_ratio > 0.6  # More than 60% caps



class CommentFlagForm(forms.ModelForm):
    """Form for flagging comments"""
    
    class Meta:
        model = CommentFlag
        fields = ['reason', 'description']
        widgets = {
            'reason': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Explain why you are reporting this comment...'
            })
        }
    
    def clean_description(self):
        """Validate flag description"""
        description = self.cleaned_data.get('description')
        if description and len(description) > 500:
            raise forms.ValidationError('Description cannot exceed 500 characters.')
        return description


class CommentSearchForm(forms.Form):
    """Form for searching comments"""
    q = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search comments...',
            'id': 'comment-search'
        }),
        label='Search'
    )
    
    def clean_q(self):
        query = self.cleaned_data.get('q')
        if query and len(query) < 2:
            raise forms.ValidationError('Search query must be at least 2 characters.')
        return query


class CommentModerationForm(forms.Form):
    """Form for comment moderation actions"""
    action = forms.ChoiceField(
        choices=[
            ('approve', 'Approve'),
            ('reject', 'Delete'),
            ('flag', 'Flag for Review'),
        ],
        widget=forms.RadioSelect
    )
    reason = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Reason for action (optional)'
        })
    )