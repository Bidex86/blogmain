# ads/templatetags/ad_tags.py
from django import template
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.urls import reverse
from ads.models import Advertisement, AdPosition
import random

register = template.Library()

@register.inclusion_tag('ads/ad_display.html', takes_context=True)
def show_ad(context, position_slug, random_selection=True):
    """Display an advertisement in the specified position"""
    request = context['request']
    current_page = request.resolver_match.url_name if request.resolver_match else None
    
    try:
        position = AdPosition.objects.get(slug=position_slug, is_active=True)
    except AdPosition.DoesNotExist:
        return {'ad': None}
    
    # Get active ads for this position
    ads = Advertisement.objects.filter(
        position=position,
        is_active=True,
        start_date__lte=timezone.now()
    ).exclude(
        end_date__lt=timezone.now()
    )
    
    # Filter based on current page context
    if current_page == 'home':
        ads = ads.filter(show_on_homepage=True)
    elif current_page in ['blogs', 'posts_by_category']:
        ads = ads.filter(show_on_blog_posts=True)
    elif current_page in ['category_posts']:
        ads = ads.filter(show_on_categories=True)
        
        # Check if we have category-specific targeting
        category_id = context.get('category_id')
        if category_id:
            category_ads = ads.filter(target_categories=category_id)
            if category_ads.exists():
                ads = category_ads
    
    # Order by priority and select
    ads = ads.order_by('-priority', '?')
    
    if random_selection and ads.exists():
        # Weighted random selection based on priority
        weights = []
        ad_list = list(ads)
        for ad in ad_list:
            weight = ad.priority * 10  # Higher priority = more likely to show
            weights.append(weight)
        
        if weights:
            selected_ad = random.choices(ad_list, weights=weights, k=1)[0]
        else:
            selected_ad = ad_list[0] if ad_list else None
    else:
        selected_ad = ads.first()
    
    return {
        'ad': selected_ad,
        'request': request,
    }

@register.simple_tag(takes_context=True)
def ad_click_url(context, ad):
    """Generate click tracking URL"""
    if not ad:
        return '#'
    
    request = context['request']
    return request.build_absolute_uri(
        reverse('ads:track_click', kwargs={'ad_id': ad.pk})
    )

@register.simple_tag
def ad_impression_pixel(ad):
    """Generate impression tracking pixel"""
    if not ad:
        return ''
    
    pixel_url = reverse('ads:track_impression', kwargs={'ad_id': ad.pk})
    return mark_safe(
        f'<img src="{pixel_url}" width="1" height="1" style="display:none;" alt="">'
    )

@register.filter
def ad_content_safe(ad):
    """Safely render ad content based on type"""
    if not ad:
        return ''
    
    if ad.ad_type == 'html':
        return mark_safe(ad.html_content)
    elif ad.ad_type == 'script':
        return mark_safe(ad.script_content)
    
    return ''

@register.inclusion_tag('ads/ad_styles.html')
def ad_styles():
    """Include CSS styles for ads"""
    return {}

@register.simple_tag
def get_ad_positions():
    """Get all available ad positions"""
    return AdPosition.objects.filter(is_active=True)