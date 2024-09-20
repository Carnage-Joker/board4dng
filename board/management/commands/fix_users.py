from django.core.management.base import BaseCommand
# Use this to get the custom user model

from board.models import UserProfile, User


class Command(BaseCommand):
    help = 'Create missing UserProfile for existing users'

    def handle(self, *args, **kwargs):
        users_without_profile = User.objects.filter(userprofile__isnull=True)
        for user in users_without_profile:
            UserProfile.objects.create(user=user)
            self.stdout.write(self.style.SUCCESS(
                f'Created UserProfile for user: {user.username}'))
        self.stdout.write(self.style.SUCCESS('All missing profiles created.'))
