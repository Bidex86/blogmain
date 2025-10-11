from django.core.management.base import BaseCommand
import nltk
import ssl

class Command(BaseCommand):
    help = 'Download required NLTK data'
    
    def handle(self, *args, **options):
        # Handle SSL issues
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context
        
        # Download required data
        downloads = [
            'punkt_tab',
            'punkt', 
            'stopwords',
            'averaged_perceptron_tagger',
            'wordnet'
        ]
        
        for item in downloads:
            try:
                nltk.download(item, quiet=False)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully downloaded {item}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Failed to download {item}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('NLTK setup complete!')
        )