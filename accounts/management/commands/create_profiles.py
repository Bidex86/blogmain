# Create this file: accounts/management/commands/create_profiles.py
# First create the directories if they don't exist:
# mkdir -p accounts/management/commands

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile

class Command(BaseCommand):
    help = 'Create profiles for users who do not have one'

    def handle(self, *args, **options):
        users_without_profiles = User.objects.filter(profile__isnull=True)
        created_count = 0
        
        for user in users_without_profiles:
            profile, created = Profile.objects.get_or_create(user=user)
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created profile for user: {user.username}')
                )
        
        if created_count == 0:
            self.stdout.write(
                self.style.WARNING('No profiles needed to be created. All users already have profiles.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} profiles.')
            )