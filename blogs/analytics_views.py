# API Views - blogs/analytics_views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .analytics import UserBehaviorAnalytics
from .models import Blog
from django.contrib.contenttypes.models import ContentType
import json

@csrf_exempt
@require_http_methods(["POST"])
def track_events(request):
    """Track multiple analytics events"""
    try:
        data = json.loads(request.body)
        events = data.get('events', [])
        
        analytics = UserBehaviorAnalytics()
        
        for event_data in events:
            # Get content object if specified
            content_object = None
            if 'content_type' in event_data and 'object_id' in event_data:
                try:
                    content_type = ContentType.objects.get(id=event_data['content_type'])
                    content_object = content_type.get_object_for_this_type(id=event_data['object_id'])
                except:
                    pass
            
            analytics.track_custom_event(
                event_type=event_data.get('event_type'),
                user_id=event_data.get('user_id'),
                session_id=event_data.get('session_id'),
                content_object=content_object,
                event_data=event_data.get('event_data', {}),
                request=request
            )
        
        return JsonResponse({'status': 'success', 'tracked': len(events)})
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def track_core_web_vitals(request):
    """Track Core Web Vitals metrics"""
    try:
        data = json.loads(request.body)
        
        analytics = UserBehaviorAnalytics()
        vitals = analytics.track_core_web_vitals(
            url=data.get('url'),
            session_id=data.get('session_id'),
            metrics={
                'lcp': data.get('lcp'),
                'fid': data.get('fid'),
                'cls': data.get('cls'),
                'fcp': data.get('fcp'),
                'ttfb': data.get('ttfb'),
            },
            request=request
        )
        
        return JsonResponse({'status': 'success', 'id': vitals.id})
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_http_methods(["GET"])
def get_performance_metrics(request):
    """Get site performance metrics"""
    try:
        days = int(request.GET.get('days', 7))
        analytics = UserBehaviorAnalytics()
        metrics = analytics.get_site_performance_metrics(days=days)
        
        return JsonResponse(metrics)
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@require_http_methods(["GET"])
def get_content_insights(request):
    """Get content performance insights"""
    try:
        days = int(request.GET.get('days', 30))
        analytics = UserBehaviorAnalytics()
        insights = analytics.get_content_performance_insights(days=days)
        
        # Convert Blog objects to serializable data
        serialized_insights = {
            'top_performing': [
                {
                    'title': insight['post'].title,
                    'slug': insight['post'].slug,
                    'views': insight['views'],
                    'engagement_score': insight['engagement_score'],
                }
                for insight in insights['top_performing']
            ],
            'content_recommendations': insights['content_recommendations']
        }
        
        return JsonResponse(serialized_insights)
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)