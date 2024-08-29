from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models


def get_default_user():
    return User.objects.first()


class PrivateMessage(models.Model):
    sender = models.ForeignKey(
        User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(
        User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Message from {self.sender} to {self.recipient}'
    

class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User, on_delete=models.SET_DEFAULT, default=get_default_user
    )
    is_moderated = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)

    def __str__(self):
        return self.title
