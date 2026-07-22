# ads/templatetags/ad_tags.py
from django import template
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.urls import reverse
from ads.models import Advertisement, AdPosition
import random
from django.template.loader import render_to_string

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

@register.simple_tag(takes_context=True)
def inject_ad_into_content(context, content, position_slug='in-content', after_paragraph=3):
    """Insert an ad into post HTML after the Nth </p>. Falls back to untouched content."""
    request = context.get('request')
    if not content or not request:
        return mark_safe(content or '')

    try:
        position = AdPosition.objects.get(slug=position_slug, is_active=True)
        ads = Advertisement.objects.filter(
            position=position, is_active=True,
            start_date__lte=timezone.now(),
        ).exclude(end_date__lt=timezone.now()).order_by('-priority', '?')
        ad = ads.first()
        if not ad:
            return mark_safe(content)

        ad_html = render_to_string('ads/ad_display.html', {'ad': ad, 'request': request})

        parts = content.split('</p>')
        # Only inject if the post is long enough to sandwich the ad in text
        if len(parts) > after_paragraph + 1:
            parts[after_paragraph - 1] += '</p>' + ad_html
            rebuilt = '</p>'.join(
                p for i, p in enumerate(parts)
                if not (i == after_paragraph - 1 and False)
            )
            # simpler correct rebuild:
            head = '</p>'.join(parts[:after_paragraph]) + '</p>'
            tail = '</p>'.join(parts[after_paragraph:])
            return mark_safe(head + ad_html + tail)
        return mark_safe(content)
    except AdPosition.DoesNotExist:
        return mark_safe(content)
    except Exception:
        return mark_safe(content)
    
@register.filter
def para_head(content, n=3):
    """First n paragraphs of HTML content (split at </p> — never mid-tag)."""
    if not content:
        return ''
    parts = content.split('</p>')
    if len(parts) <= n + 1:
        return mark_safe(content)          # short post: whole thing is the head
    return mark_safe('</p>'.join(parts[:n]) + '</p>')

@register.filter
def para_tail(content, n=3):
    """Everything after the first n paragraphs; empty for short posts."""
    if not content:
        return ''
    parts = content.split('</p>')
    if len(parts) <= n + 1:
        return ''                          # short post: tail is empty, head had it all
    return mark_safe('</p>'.join(parts[n:]))