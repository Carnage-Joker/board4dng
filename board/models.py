from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


def get_default_user():
    """Returns the first user in the database as the default."""
    return User.objects.first()


class UserManager(BaseUserManager):
    """Custom manager for handling user creation, including superusers."""

    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')

        email = self.normalize_email(email)
        user = self.model(email=email, username=username)
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
    """Custom user model."""

    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    is_moderator = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    email_notifications = models.BooleanField(default=True)
    fcm_token = models.CharField(max_length=255, blank=True, null=True)
    is_trusted_user = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username


class PrivateMessage(models.Model):
    """Model for private messages between users."""

    sender = models.ForeignKey(
        User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(
        User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Message from {self.sender} to {self.recipient}'


class Post(models.Model):
    """Model for posts in the message board."""

    title = models.CharField(max_length=100)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_flagged = models.BooleanField(default=False)
    is_moderated = models.BooleanField(default=False)
    is_trusted_user = models.BooleanField(
        default=False)  # Bypass moderation if trusted

    def __str__(self):
        # Return first 20 characters for admin display
        return self.content[:20]


class UserProfile(models.Model):
    """Extended user profile model."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_notifications = models.BooleanField(default=True)
    in_app_notifications = models.BooleanField(default=True)
    selected_theme = models.CharField(
        max_length=20,
        choices=[
            ('default', 'Default'),
            ('neon', 'Neon'),
            ('dark', 'Dark'),
            ('blue', 'Electric Blue'),
            ('purple', 'Electric Purple')
        ],
        default='default'
    )
    privacy_mode = models.BooleanField(default=False)
    message_preview = models.BooleanField(default=True)
    auto_logout = models.BooleanField(default=False)
    location_sharing = models.BooleanField(default=False)
    profile_visibility = models.BooleanField(default=True)

    def __str__(self):
        return f'Profile of {self.user.username}'
