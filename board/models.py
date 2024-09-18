
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.db import models
from django.utils import timezone


def get_default_user():
    return User.objects.first()


class UserManager(BaseUserManager):
    # Custom manager for handling user creation, including superusers
    def create_user(self, email, username, password=None):
        if email is None:
            raise ValueError('Users must have an email address')
        if username is None:
            raise ValueError('Users must have a username')

        user = self.model(email=self.normalize_email(email), username=username)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None):
        user = self.create_user(
            email=email, username=username, password=password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    is_moderator = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)  # Add this line
    email_notifications = models.BooleanField(default=True)  # Toggle for email notifications
    fcm_token = models.CharField(max_length=255, blank=True, null=True)  # Token for push notifications

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username


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
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_flagged = models.BooleanField(default=False)
    is_moderated = models.BooleanField(default=False)
    is_trusted_user = models.BooleanField(default=False)

    def __str__(self):
        return self.content[:20]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_notifications = models.BooleanField(default=True)
    in_app_notifications = models.BooleanField(default=True)
    selected_theme = models.CharField(
        max_length=20,
        choices=[('default', 'Default'), ('neon', 'Neon'), ('dark', 'Dark'),
                 ('blue', 'Electric Blue'), ('purple', 'Electric Purple')],
        default='default'
    )
    # Other settings (add more if needed)
    privacy_mode = models.BooleanField(default=False)
    message_preview = models.BooleanField(default=True)
    auto_logout = models.BooleanField(default=False)
    location_sharing = models.BooleanField(default=False)
    profile_visibility = models.BooleanField(default=True)
