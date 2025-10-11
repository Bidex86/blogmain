# ads/forms.py (Optional - for enhanced admin experience)
from django import forms
from django.core.exceptions import ValidationError
from .models import Advertisement, AdPosition
import re

class AdvertisementAdminForm(forms.ModelForm):
    """Enhanced form for advertisement admin"""
    
    class Meta:
        model = Advertisement
        fields = '__all__'
        widgets = {
            'html_content': forms.Textarea(attrs={
                'rows': 10, 
                'cols': 80,
                'placeholder': 'Enter your HTML content here...\nExample:\n<div class="my-ad">\n  <h3>Your Ad Title</h3>\n  <p>Ad description</p>\n</div>'
            }),
            'script_content': forms.Textarea(attrs={
                'rows': 10, 
                'cols': 80,
                'placeholder': 'Enter JavaScript or third-party ad code here...\nExample:\n<script>\n  // Your ad script\n  console.log("Ad loaded");\n</script>\n\nOr Google Ads code:\n<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>\n<ins class="adsbygoogle" ...></ins>'
            }),
            'alt_text': forms.TextInput(attrs={
                'placeholder': 'Alternative text for images (accessibility)'
            }),
            'click_url': forms.URLInput(attrs={
                'placeholder': 'https://example.com/landing-page'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add helpful text to fields
        self.fields['html_content'].help_text = (
            "HTML content for rich ads. Can include CSS styling. "
            "Use responsibly - malicious code will be filtered."
        )
        self.fields['script_content'].help_text = (
            "JavaScript code or third-party ad codes (Google Ads, etc.). "
            "Ensure scripts are from trusted sources only."
        )
        self.fields['position'].help_text = "Choose where this ad will be displayed"
        self.fields['priority'].help_text = "Higher priority ads are shown more frequently"
        
        # Make some fields required based on ad type
        if self.instance and self.instance.pk:
            ad_type = self.instance.ad_type
            if ad_type == 'image':
                self.fields['image'].required = True
            elif ad_type == 'html':
                self.fields['html_content'].required = True
            elif ad_type == 'script':
                self.fields['script_content'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        ad_type = cleaned_data.get('ad_type')
        image = cleaned_data.get('image')
        html_content = cleaned_data.get('html_content')
        script_content = cleaned_data.get('script_content')
        
        # Validate that required content exists for each ad type
        if ad_type == 'image' and not image:
            raise ValidationError("Image is required for image ads.")
        
        if ad_type == 'html' and not html_content:
            raise ValidationError("HTML content is required for HTML ads.")
        
        if ad_type == 'script' and not script_content:
            raise ValidationError("Script content is required for script ads.")
        
        # Basic security check for script content
        if script_content:
            self._validate_script_content(script_content)
        
        # Basic HTML validation
        if html_content:
            self._validate_html_content(html_content)
        
        return cleaned_data
    
    def _validate_script_content(self, content):
        """Basic validation for script content"""
        # Check for potentially dangerous patterns
        dangerous_patterns = [
            r'document\.write\s*\(',
            r'eval\s*\(',
            r'innerHTML\s*=',
            r'document\.cookie',
            r'localStorage\.clear',
            r'sessionStorage\.clear',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                raise ValidationError(
                    f"Potentially unsafe JavaScript detected. "
                    f"Please review your script for security issues."
                )
    
    def _validate_html_content(self, content):
        """Basic validation for HTML content"""
        # Check for script tags in HTML (should use script_content instead)
        if '<script' in content.lower():
            raise ValidationError(
                "Script tags detected in HTML content. "
                "Please use the 'Script Content' field for JavaScript."
            )

class AdPositionAdminForm(forms.ModelForm):
    """Enhanced form for ad position admin"""
    
    class Meta:
        model = AdPosition
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add helpful text
        self.fields['width'].help_text = "Width in pixels (e.g., 728 for leaderboard)"
        self.fields['height'].help_text = "Height in pixels (e.g., 90 for leaderboard)"
        self.fields['slug'].help_text = "URL-friendly identifier (auto-generated from name)"
    
    def clean_slug(self):
        slug = self.cleaned_data['slug']
        
        # Check for reserved slugs
        reserved_slugs = ['admin', 'api', 'ads', 'static', 'media']
        if slug in reserved_slugs:
            raise ValidationError(f"'{slug}' is a reserved slug. Please choose another.")
        
        return slug