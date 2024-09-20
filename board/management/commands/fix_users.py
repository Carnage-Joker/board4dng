from django.core.management.base import BaseCommand
from board.models import UserProfile, User


class Command(BaseCommand):
    help = 'Create missing user profiles for users'

    def handle(self, *args, **kwargs):
        users_without_profile = User.objects.filter(userprofile__isnull=True)
        for user in users_without_profile:
            UserProfile.objects.create(user=user)
            self.stdout.write(self.style.SUCCESS(
                f"Created profile for {user.username}"))

        self.stdout.write(self.style.SUCCESS(
            'Successfully created missing user profiles.'))
