# blogs/analytics.py
import json
from datetime import datetime, timedelta
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.conf import settings
import requests

class AnalyticsEvent(models.Model):
    """Custom analytics events"""
    EVENT_TYPES = [
        ('page_view', 'Page View'),
        ('article_read', 'Article Read'),
        ('comment_posted', 'Comment Posted'),
        ('newsletter_signup', 'Newsletter Signup'),
        ('search_performed', 'Search Performed'),
        ('link_clicked', 'Link Clicked'),
        ('download', 'Download'),
        ('scroll_depth', 'Scroll Depth'),
        ('time_on_page', 'Time on Page'),
        ('voice_search', 'Voice Search'),
    ]
    
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    user_id = models.CharField(max_length=255, blank=True)  # Anonymous user tracking
    session_id = models.CharField(max_length=255)
    
    # Content reference
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Event data
    event_data = models.JSONField(default=dict)
    
    # User context
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    referrer = models.URLField(blank=True)
    
    # Timing
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['session_id']),
        ]

class CoreWebVitals(models.Model):
    """Track Core Web Vitals metrics"""
    url = models.URLField()
    session_id = models.CharField(max_length=255)
    
    # Core Web Vitals
    lcp = models.FloatField(null=True, blank=True)  # Largest Contentful Paint
    fid = models.FloatField(null=True, blank=True)  # First Input Delay
    cls = models.FloatField(null=True, blank=True)  # Cumulative Layout Shift
    
    # Additional metrics
    fcp = models.FloatField(null=True, blank=True)  # First Contentful Paint
    ttfb = models.FloatField(null=True, blank=True)  # Time to First Byte
    
    # Device info
    device_type = models.CharField(max_length=50, blank=True)
    connection_type = models.CharField(max_length=50, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['url', 'timestamp']),
        ]

class UserBehaviorAnalytics:
    """Advanced user behavior analytics"""
    
    def __init__(self):
        self.ga4_measurement_id = getattr(settings, 'GA4_MEASUREMENT_ID', None)
        self.ga4_api_secret = getattr(settings, 'GA4_API_SECRET', None)
    
    def track_custom_event(self, event_type, user_id=None, session_id=None, 
                          content_object=None, event_data=None, request=None):
        """Track custom analytics event"""
        
        # Create database record
        event = AnalyticsEvent(
            event_type=event_type,
            user_id=user_id or '',
            session_id=session_id or '',
            event_data=event_data or {},
        )
        
        if content_object:
            event.content_type = ContentType.objects.get_for_model(content_object)
            event.object_id = content_object.id
        
        if request:
            event.user_agent = request.META.get('HTTP_USER_AGENT', '')
            event.ip_address = self.get_client_ip(request)
            event.referrer = request.META.get('HTTP_REFERER', '')
        
        event.save()
        
        # Send to GA4 if configured
        if self.ga4_measurement_id and self.ga4_api_secret:
            self.send_to_ga4(event_type, user_id, event_data)
        
        return event
    
    def send_to_ga4(self, event_name, user_id=None, event_data=None):
        """Send event to Google Analytics 4"""
        if not self.ga4_measurement_id or not self.ga4_api_secret:
            return
        
        url = f"https://www.google-analytics.com/mp/collect?measurement_id={self.ga4_measurement_id}&api_secret={self.ga4_api_secret}"
        
        payload = {
            "client_id": user_id or "anonymous",
            "events": [{
                "name": event_name,
                "params": event_data or {}
            }]
        }
        
        try:
            requests.post(url, json=payload, timeout=5)
        except requests.exceptions.RequestException:
            pass  # Fail silently for analytics
    
    def track_core_web_vitals(self, url, session_id, metrics, request=None):
        """Track Core Web Vitals metrics"""
        vitals = CoreWebVitals(
            url=url,
            session_id=session_id,
            lcp=metrics.get('lcp'),
            fid=metrics.get('fid'),
            cls=metrics.get('cls'),
            fcp=metrics.get('fcp'),
            ttfb=metrics.get('ttfb'),
        )
        
        if request:
            vitals.device_type = self.get_device_type(request)
            vitals.connection_type = self.get_connection_type(request)
        
        vitals.save()
        return vitals
    
    def get_reading_analytics(self, blog_post, days=30):
        """Get detailed reading analytics for a blog post"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        content_type = ContentType.objects.get_for_model(blog_post)
        
        # Get all events for this post
        events = AnalyticsEvent.objects.filter(
            content_type=content_type,
            object_id=blog_post.id,
            timestamp__gte=start_date
        )
        
        analytics = {
            'total_views': events.filter(event_type='page_view').count(),
            'unique_visitors': events.filter(event_type='page_view').values('user_id').distinct().count(),
            'avg_time_on_page': self._calculate_avg_time_on_page(events),
            'scroll_depth': self._calculate_avg_scroll_depth(events),
            'engagement_rate': self._calculate_engagement_rate(events),
            'bounce_rate': self._calculate_bounce_rate(events),
            'conversion_events': events.exclude(event_type__in=['page_view', 'scroll_depth', 'time_on_page']).count(),
            'daily_views': self._get_daily_views(events),
            'referrer_analysis': self._analyze_referrers(events),
            'device_breakdown': self._analyze_devices(events),
        }
        
        return analytics
    
    def get_site_performance_metrics(self, days=7):
        """Get overall site performance metrics"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Core Web Vitals analysis
        vitals = CoreWebVitals.objects.filter(timestamp__gte=start_date)
        
        performance_metrics = {
            'core_web_vitals': {
                'lcp': {
                    'avg': vitals.exclude(lcp__isnull=True).aggregate(avg=models.Avg('lcp'))['avg'] or 0,
                    'p75': self._calculate_percentile(vitals.values_list('lcp', flat=True), 75),
                    'good_ratio': vitals.filter(lcp__lt=2.5).count() / max(vitals.count(), 1)
                },
                'fid': {
                    'avg': vitals.exclude(fid__isnull=True).aggregate(avg=models.Avg('fid'))['avg'] or 0,
                    'p75': self._calculate_percentile(vitals.values_list('fid', flat=True), 75),
                    'good_ratio': vitals.filter(fid__lt=100).count() / max(vitals.count(), 1)
                },
                'cls': {
                    'avg': vitals.exclude(cls__isnull=True).aggregate(avg=models.Avg('cls'))['avg'] or 0,
                    'p75': self._calculate_percentile(vitals.values_list('cls', flat=True), 75),
                    'good_ratio': vitals.filter(cls__lt=0.1).count() / max(vitals.count(), 1)
                }
            },
            'page_speed': {
                'fcp_avg': vitals.exclude(fcp__isnull=True).aggregate(avg=models.Avg('fcp'))['avg'] or 0,
                'ttfb_avg': vitals.exclude(ttfb__isnull=True).aggregate(avg=models.Avg('ttfb'))['avg'] or 0,
            },
            'device_performance': self._analyze_device_performance(vitals),
            'recommendations': self._generate_performance_recommendations(vitals)
        }
        
        return performance_metrics
    
    def get_content_performance_insights(self, days=30):
        """Get insights on content performance"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        from blogs.models import Blog
        
        # Get all published posts
        posts = Blog.objects.filter(status='Published')
        content_type = ContentType.objects.get_for_model(Blog)
        
        insights = []
        
        for post in posts:
            post_events = AnalyticsEvent.objects.filter(
                content_type=content_type,
                object_id=post.id,
                timestamp__gte=start_date
            )
            
            if post_events.exists():
                post_analytics = {
                    'post': post,
                    'views': post_events.filter(event_type='page_view').count(),
                    'unique_visitors': post_events.filter(event_type='page_view').values('user_id').distinct().count(),
                    'avg_time': self._calculate_avg_time_on_page(post_events),
                    'engagement_score': self._calculate_engagement_score(post_events),
                    'conversion_rate': self._calculate_conversion_rate(post_events),
                }
                insights.append(post_analytics)
        
        # Sort by engagement score
        insights.sort(key=lambda x: x['engagement_score'], reverse=True)
        
        return {
            'top_performing': insights[:10],
            'underperforming': [p for p in insights if p['engagement_score'] < 30][-10:],
            'content_recommendations': self._generate_content_recommendations(insights)
        }
    
    def _calculate_avg_time_on_page(self, events):
        """Calculate average time spent on page"""
        time_events = events.filter(event_type='time_on_page')
        if not time_events.exists():
            return 0
        
        total_time = sum(
            event.event_data.get('duration', 0) 
            for event in time_events 
            if 'duration' in event.event_data
        )
        
        return total_time / time_events.count() if time_events.count() > 0 else 0
    
    def _calculate_avg_scroll_depth(self, events):
        """Calculate average scroll depth"""
        scroll_events = events.filter(event_type='scroll_depth')
        if not scroll_events.exists():
            return 0
        
        total_depth = sum(
            event.event_data.get('depth', 0) 
            for event in scroll_events 
            if 'depth' in event.event_data
        )
        
        return total_depth / scroll_events.count() if scroll_events.count() > 0 else 0
    
    def _calculate_engagement_rate(self, events):
        """Calculate engagement rate"""
        total_sessions = events.values('session_id').distinct().count()
        if total_sessions == 0:
            return 0
        
        engaged_sessions = events.filter(
            event_type__in=['comment_posted', 'newsletter_signup', 'link_clicked']
        ).values('session_id').distinct().count()
        
        return (engaged_sessions / total_sessions) * 100
    
    def _calculate_bounce_rate(self, events):
        """Calculate bounce rate"""
        total_sessions = events.values('session_id').distinct().count()
        if total_sessions == 0:
            return 0
        
        # Sessions with only one page view and no other interactions
        single_page_sessions = 0
        for session_id in events.values_list('session_id', flat=True).distinct():
            session_events = events.filter(session_id=session_id)
            if session_events.count() == 1 and session_events.first().event_type == 'page_view':
                single_page_sessions += 1
        
        return (single_page_sessions / total_sessions) * 100
    
    def _get_daily_views(self, events):
        """Get daily view counts"""
        daily_views = events.filter(event_type='page_view').extra(
            select={'day': 'date(timestamp)'}
        ).values('day').annotate(views=models.Count('id')).order_by('day')
        
        return list(daily_views)
    
    def _analyze_referrers(self, events):
        """Analyze referrer sources"""
        referrers = events.exclude(referrer='').values('referrer').annotate(
            count=models.Count('id')
        ).order_by('-count')[:10]
        
        return list(referrers)
    
    def _analyze_devices(self, events):
        """Analyze device types"""
        # This would require parsing user agents - simplified version
        devices = {'mobile': 0, 'desktop': 0, 'tablet': 0}
        
        for event in events:
            user_agent = event.user_agent.lower()
            if 'mobile' in user_agent:
                devices['mobile'] += 1
            elif 'tablet' in user_agent:
                devices['tablet'] += 1
            else:
                devices['desktop'] += 1
        
        return devices
    
    def _calculate_percentile(self, values, percentile):
        """Calculate percentile for a list of values"""
        clean_values = [v for v in values if v is not None]
        if not clean_values:
            return 0
        
        clean_values.sort()
        index = int((percentile / 100) * len(clean_values))
        return clean_values[min(index, len(clean_values) - 1)]
    
    def _analyze_device_performance(self, vitals):
        """Analyze performance by device type"""
        devices = {}
        
        for device_type in ['mobile', 'desktop', 'tablet']:
            device_vitals = vitals.filter(device_type=device_type)
            if device_vitals.exists():
                devices[device_type] = {
                    'lcp_avg': device_vitals.exclude(lcp__isnull=True).aggregate(avg=models.Avg('lcp'))['avg'] or 0,
                    'fid_avg': device_vitals.exclude(fid__isnull=True).aggregate(avg=models.Avg('fid'))['avg'] or 0,
                    'cls_avg': device_vitals.exclude(cls__isnull=True).aggregate(avg=models.Avg('cls'))['avg'] or 0,
                }
        
        return devices
    
    def _generate_performance_recommendations(self, vitals):
        """Generate performance improvement recommendations"""
        recommendations = []
        
        avg_lcp = vitals.exclude(lcp__isnull=True).aggregate(avg=models.Avg('lcp'))['avg'] or 0
        avg_fid = vitals.exclude(fid__isnull=True).aggregate(avg=models.Avg('fid'))['avg'] or 0
        avg_cls = vitals.exclude(cls__isnull=True).aggregate(avg=models.Avg('cls'))['avg'] or 0
        
        if avg_lcp > 2.5:
            recommendations.append({
                'metric': 'LCP',
                'issue': f'LCP is {avg_lcp:.2f}s (should be < 2.5s)',
                'suggestions': [
                    'Optimize images with WebP format and responsive sizing',
                    'Use preload for critical resources',
                    'Minimize server response times',
                    'Remove unused CSS and JavaScript'
                ]
            })
        
        if avg_fid > 100:
            recommendations.append({
                'metric': 'FID',
                'issue': f'FID is {avg_fid:.2f}ms (should be < 100ms)',
                'suggestions': [
                    'Break up long-running JavaScript tasks',
                    'Use web workers for heavy computations',
                    'Defer non-critical JavaScript',
                    'Optimize third-party scripts'
                ]
            })
        
        if avg_cls > 0.1:
            recommendations.append({
                'metric': 'CLS',
                'issue': f'CLS is {avg_cls:.3f} (should be < 0.1)',
                'suggestions': [
                    'Set explicit dimensions for images and videos',
                    'Reserve space for ads and embeds',
                    'Use transform animations instead of layout-triggering properties',
                    'Preload fonts to prevent layout shifts'
                ]
            })
        
        return recommendations
    
    def _calculate_engagement_score(self, events):
        """Calculate overall engagement score"""
        if not events.exists():
            return 0
        
        score = 0
        
        # Time on page (0-40 points)
        avg_time = self._calculate_avg_time_on_page(events)
        score += min(avg_time / 300 * 40, 40)  # Max 40 points for 5+ minutes
        
        # Scroll depth (0-30 points)
        avg_scroll = self._calculate_avg_scroll_depth(events)
        score += min(avg_scroll / 100 * 30, 30)  # Max 30 points for 100% scroll
        
        # Interactions (0-30 points)
        interaction_events = events.exclude(event_type__in=['page_view', 'scroll_depth', 'time_on_page'])
        interaction_rate = interaction_events.count() / events.count() if events.count() > 0 else 0
        score += min(interaction_rate * 100, 30)
        
        return round(score, 1)
    
    def _calculate_conversion_rate(self, events):
        """Calculate conversion rate"""
        total_sessions = events.values('session_id').distinct().count()
        if total_sessions == 0:
            return 0
        
        conversion_events = events.filter(
            event_type__in=['newsletter_signup', 'comment_posted', 'download']
        ).values('session_id').distinct().count()
        
        return (conversion_events / total_sessions) * 100
    
    def _generate_content_recommendations(self, insights):
        """Generate content optimization recommendations"""
        recommendations = []
        
        if insights:
            avg_engagement = sum(p['engagement_score'] for p in insights) / len(insights)
            
            if avg_engagement < 50:
                recommendations.append({
                    'type': 'engagement',
                    'message': f'Average engagement score is {avg_engagement:.1f}. Consider adding more interactive elements.',
                    'actions': [
                        'Add more questions and calls-to-action',
                        'Include relevant images and media',
                        'Break up long paragraphs',
                        'Add internal links to related content'
                    ]
                })
            
            high_bounce_posts = [p for p in insights if self._calculate_bounce_rate_for_post(p) > 70]
            if high_bounce_posts:
                recommendations.append({
                    'type': 'bounce_rate',
                    'message': f'{len(high_bounce_posts)} posts have high bounce rates (>70%)',
                    'actions': [
                        'Improve page loading speed',
                        'Make content more engaging in the first paragraph',
                        'Add related content suggestions',
                        'Optimize for mobile viewing'
                    ]
                })
        
        return recommendations
    
    def _calculate_bounce_rate_for_post(self, post_analytics):
        """Calculate bounce rate for a specific post"""
        # This would need the actual events - simplified calculation
        return 60  # Placeholder
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_device_type(self, request):
        """Determine device type from user agent"""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        if 'mobile' in user_agent:
            return 'mobile'
        elif 'tablet' in user_agent:
            return 'tablet'
        else:
            return 'desktop'
    
    def get_connection_type(self, request):
        """Get connection type if available"""
        # This would require additional headers or JavaScript detection
        return request.META.get('HTTP_NETWORK_TYPE', 'unknown')


# JavaScript for client-side analytics
# static/js/analytics-manager.js
