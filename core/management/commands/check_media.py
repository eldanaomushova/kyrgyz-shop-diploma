from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Check media directories'

    def handle(self, *args, **options):
        self.stdout.write(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
        self.stdout.write(f"MEDIA_ROOT exists: {os.path.exists(settings.MEDIA_ROOT)}")
        
        if not os.path.exists(settings.MEDIA_ROOT):
            self.stdout.write(self.style.WARNING("Creating MEDIA_ROOT..."))
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        
        tryon_dir = os.path.join(settings.MEDIA_ROOT, 'tryon_results')
        self.stdout.write(f"Tryon dir: {tryon_dir}")
        self.stdout.write(f"Tryon dir exists: {os.path.exists(tryon_dir)}")
        
        if not os.path.exists(tryon_dir):
            self.stdout.write(self.style.WARNING("Creating tryon_results directory..."))
            os.makedirs(tryon_dir, exist_ok=True)
        
        self.stdout.write(self.style.SUCCESS("Directories are ready!"))