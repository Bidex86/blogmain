# ads/management/commands/cleanup_expired_ads.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from ads.models import Advertisement

class Command(BaseCommand):
    help = 'Deactivate expired advertisements'

    def handle(self, *args, **options):
        expired_ads = Advertisement.objects.filter(
            end_date__lt=timezone.now(),
            is_active=True
        )
        
        count = expired_ads.count()
        expired_ads.update(is_active=False)
        
        self.stdout.write(
            self.style.SUCCESS(f'Deactivated {count} expired advertisements')
        )
