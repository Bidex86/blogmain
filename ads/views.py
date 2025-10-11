# ads/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q
from .models import Advertisement, AdClick, AdImpression
import json
from datetime import datetime, timedelta

@never_cache
def track_impression(request, ad_id):
    """Track ad impression via pixel"""
    try:
        ad = Advertisement.objects.get(pk=ad_id, is_active=True)
        
        # Create impression record
        AdImpression.objects.create(
            advertisement=ad,
            ip_address=get_client_ip(request),
            page_url=request.META.get('HTTP_REFERER', ''),
            user=request.user if request.user.is_authenticated else None
        )
        
        # Increment counter
        ad.increment_impressions()
        
    except Advertisement.DoesNotExist:
        pass
    
    # Return 1x1 transparent pixel
    pixel_data = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00\x3B'
    response = HttpResponse(pixel_data, content_type='image/gif')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

@never_cache
def track_click(request, ad_id):
    """Track ad click and redirect"""
    try:
        ad = get_object_or_404(Advertisement, pk=ad_id, is_active=True)
        
        # Create click record
        AdClick.objects.create(
            advertisement=ad,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            referer=request.META.get('HTTP_REFERER', ''),
            user=request.user if request.user.is_authenticated else None
        )
        
        # Increment counter
        ad.increment_clicks()
        
        # Redirect to target URL
        if ad.click_url:
            return redirect(ad.click_url)
        
    except Advertisement.DoesNotExist:
        pass
    
    return redirect('/')

@staff_member_required
def ad_analytics(request):
    """Display ad analytics dashboard"""
    # Get date range from query params
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Analytics data
    ads_performance = Advertisement.objects.filter(
        created_at__gte=start_date
    ).order_by('-impressions')
    
    # Top performing ads
    top_ads = ads_performance[:10]
    
    # Calculate totals
    total_impressions = sum(ad.impressions for ad in Advertisement.objects.all())
    total_clicks = sum(ad.clicks for ad in Advertisement.objects.all())
    
    # Calculate overall CTR
    if total_impressions > 0:
        overall_ctr = (total_clicks / total_impressions) * 100
    else:
        overall_ctr = 0
    
    # Position performance with CTR calculation
    position_stats = {}
    for ad in Advertisement.objects.all():
        pos = ad.position.name
        if pos not in position_stats:
            position_stats[pos] = {'impressions': 0, 'clicks': 0, 'ads': 0}
        position_stats[pos]['impressions'] += ad.impressions
        position_stats[pos]['clicks'] += ad.clicks
        position_stats[pos]['ads'] += 1
    
    # Calculate CTR for each position
    for pos_name, stats in position_stats.items():
        if stats['impressions'] > 0:
            stats['ctr'] = (stats['clicks'] / stats['impressions']) * 100
        else:
            stats['ctr'] = 0
    
    context = {
        'ads_performance': ads_performance,
        'top_ads': top_ads,
        'position_stats': position_stats,
        'days': days,
        'total_impressions': total_impressions,
        'total_clicks': total_clicks,
        'overall_ctr': overall_ctr,
    }
    
    return render(request, 'ads/analytics.html', context)

@csrf_exempt
def ad_ajax_impression(request):
    """AJAX endpoint for impression tracking"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ad_id = data.get('ad_id')
            
            ad = Advertisement.objects.get(pk=ad_id, is_active=True)
            
            AdImpression.objects.create(
                advertisement=ad,
                ip_address=get_client_ip(request),
                page_url=data.get('page_url', ''),
                user=request.user if request.user.is_authenticated else None
            )
            
            ad.increment_impressions()
            
            return JsonResponse({'success': True})
            
        except (Advertisement.DoesNotExist, json.JSONDecodeError):
            pass
    
    return JsonResponse({'success': False})

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip