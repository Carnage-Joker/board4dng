from django.db import models
from django.contrib.auth.models import User

from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings


def get_default_user():
    return User.objects.first()


class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User, on_delete=models.SET_DEFAULT, default=get_default_user
    )
    is_moderated = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)

    def send_to_moderator(self):
        # Logic to send an email to a moderator if a post is flagged as offensive
        subject = f"Moderation needed for post: {self.title}"
        message = f"The following post needs moderation:\n\nTitle: {
            self.title}\n\nContent: {self.content}\n\nAuthor: {self.author.username}"
        moderator_email = "moderator@example.com"  # Replace with actual moderator email

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,  # Typically defined in settings.py
            [moderator_email],
        )

    def __str__(self):
        return self.title
