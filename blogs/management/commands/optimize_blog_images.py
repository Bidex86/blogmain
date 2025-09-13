# blogs/management/commands/optimize_blog_images.py

from django.core.management.base import BaseCommand
from blogs.models import Blog
from PIL import Image
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Optimize blog images for better performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quality',
            type=int,
            default=85,
            help='JPEG quality (default: 85)',
        )
        parser.add_argument(
            '--max-width',
            type=int,
            default=1200,
            help='Maximum width for images (default: 1200px)',
        )

    def handle(self, *args, **options):
        quality = options['quality']
        max_width = options['max_width']
        
        self.stdout.write(f'Starting image optimization (quality: {quality}, max-width: {max_width}px)')
        
        optimized_count = 0
        error_count = 0
        
        blogs = Blog.objects.filter(featured_image__isnull=False)
        
        for blog in blogs:
            try:
                if self.optimize_image(blog.featured_image.path, quality, max_width):
                    optimized_count += 1
                    self.stdout.write(f'✓ Optimized: {blog.title}')
                
            except Exception as e:
                error_count += 1
                self.stdout.write(f'✗ Error optimizing {blog.title}: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Optimization complete! '
                f'Optimized: {optimized_count}, Errors: {error_count}'
            )
        )

    def optimize_image(self, image_path, quality, max_width):
        """Optimize a single image"""
        if not os.path.exists(image_path):
            return False
            
        try:
            with Image.open(image_path) as img:
                # Get original size
                original_size = os.path.getsize(image_path)
                
                # Skip if already optimized (small file)
                if original_size < 100000:  # 100KB
                    return False
                
                # Resize if too large
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Save with optimization
                img.save(
                    image_path,
                    'JPEG',
                    quality=quality,
                    optimize=True,
                    progressive=True
                )
                
                # Check if optimization was beneficial
                new_size = os.path.getsize(image_path)
                if new_size < original_size:
                    savings = ((original_size - new_size) / original_size) * 100
                    self.stdout.write(f'  Saved {savings:.1f}% ({original_size} → {new_size} bytes)')
                    return True
                
        except Exception as e:
            raise Exception(f'Failed to optimize image: {str(e)}')
        
        return False
