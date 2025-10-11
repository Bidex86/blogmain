# ads/management/commands/ad_report.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from ads.models import Advertisement, AdPosition

class Command(BaseCommand):
    help = 'Generate advertisement performance report'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to include in report'
        )

    def handle(self, *args, **options):
        days = options['days']
        start_date = timezone.now() - timedelta(days=days)
        
        self.stdout.write(f'Advertisement Performance Report ({days} days)')
        self.stdout.write('=' * 50)
        
        # Overall stats
        total_impressions = sum(ad.impressions for ad in Advertisement.objects.all())
        total_clicks = sum(ad.clicks for ad in Advertisement.objects.all())
        overall_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        
        self.stdout.write(f'Total Impressions: {total_impressions:,}')
        self.stdout.write(f'Total Clicks: {total_clicks:,}')
        self.stdout.write(f'Overall CTR: {overall_ctr:.2f}%')
        self.stdout.write('')
        
        # Top performing ads
        self.stdout.write('Top Performing Ads:')
        self.stdout.write('-' * 30)
        
        top_ads = Advertisement.objects.filter(
            impressions__gt=0
        ).order_by('-impressions')[:10]
        
        for ad in top_ads:
            ctr = ad.click_through_rate
            self.stdout.write(
                f'{ad.title[:30]:30} | {ad.impressions:6,} imp | {ad.clicks:4} clicks | {ctr:5.2f}% CTR'
            )
        
        # Position performance
        self.stdout.write('')
        self.stdout.write('Position Performance:')
        self.stdout.write('-' * 30)
        
        for position in AdPosition.objects.all():
            ads = Advertisement.objects.filter(position=position)
            pos_impressions = sum(ad.impressions for ad in ads)
            pos_clicks = sum(ad.clicks for ad in ads)
            pos_ctr = (pos_clicks / pos_impressions * 100) if pos_impressions > 0 else 0
            
            self.stdout.write(
                f'{position.name[:20]:20} | {pos_impressions:6,} imp | {pos_clicks:4} clicks | {pos_ctr:5.2f}% CTR'
            )