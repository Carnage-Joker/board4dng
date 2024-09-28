from datetime import timedelta
from .utils import send_to_moderator  # Assuming you have a utility for this
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings


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
    is_approved = models.BooleanField(default=False)
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

    def flag_for_moderation(self, banned_word):
        """Flags the post for moderation and notifies moderators."""
        self.is_flagged = True
        self.is_moderated = False  # Needs review by a moderator
        self.save()

        # Notify moderators with information about the banned word
        send_to_moderator(self, reason=f"Flagged due to banned word: {banned_word}")

    def send_creation_notification(self):
        """Send email notification to all users except the author."""
        all_user_emails = User.objects.exclude(id=self.author.id).exclude(email='').values_list('email', flat=True)

        send_mail(
            subject='New Post Created',
            message=f"A new post has been created by {self.author.username}.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=list(all_user_emails),
            fail_silently=False,
        )

    def __str__(self):
        return f"Post: {self.title} by {self.author.username if self.author else 'Unknown'}"


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
    is_trusted_user = models.BooleanField(default=False)
    
    def __str__(self):
        return f'Profile of {self.user.username}'


class Habit(models.Model):
    FREQUENCY_CHOICES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    start_date = models.DateField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    frequency = models.CharField(
        max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    current_count = models.IntegerField(default=0)
    target_count = models.IntegerField(default=1)
    # Correctly set as a date field with default
    reset_date = models.DateField(default=timezone.now)

    def save(self, *args, **kwargs):
        """Override save to set reset_date based on frequency if not already set."""
        if not self.reset_date:
            self.reset_date = self.calculate_reset_date()
        super().save(*args, **kwargs)

    def calculate_reset_date(self):
        """Calculate the next reset date based on the frequency."""
        now = timezone.now()

        if self.frequency == 'hourly':
            return now + timedelta(hours=1)
        elif self.frequency == 'daily':
            return now + timedelta(days=1)
        elif self.frequency == 'weekly':
            return now + timedelta(weeks=1)
        elif self.frequency == 'monthly':
            # This will never fail
            next_month = now.replace(day=28) + timedelta(days=4)
            # Get the first day of the next month
            return next_month.replace(day=1).date()
        elif self.frequency == 'yearly':
            return now.replace(year=now.year + 1).date()
        return now.date()  # Default to today if no valid frequency

    def increment_count(self):
        """Increments the current count and checks if the habit is completed."""
        self.reset_if_needed()

        if self.current_count < self.target_count:
            self.current_count += 1
            self.save()

        if self.current_count >= self.target_count:
            self.completed = True
            self.save()

    def reset_if_needed(self):
        """Resets the habit's count based on the frequency."""
        now = timezone.now()

        if self.frequency == 'hourly' and now >= self.reset_date:
            self.current_count = 0
            self.reset_date = now + timedelta(hours=1)

        elif self.frequency == 'daily' and now.date() >= self.reset_date:
            self.current_count = 0
            self.reset_date = now.date() + timedelta(days=1)

        elif self.frequency == 'weekly' and now.date() >= self.reset_date:
            self.current_count = 0
            self.reset_date = now.date() + timedelta(weeks=1)

        elif self.frequency == 'monthly' and now.date() >= self.reset_date:
            self.current_count = 0
            next_month = now.replace(day=28) + timedelta(days=4)
            self.reset_date = next_month.replace(day=1).date()

        elif self.frequency == 'yearly' and now.date() >= self.reset_date:
            self.current_count = 0
            self.reset_date = now.replace(year=now.year + 1).date()

        self.completed = False
        self.save()


class HabitProgress(models.Model):
    habit = models.ForeignKey(
            Habit, on_delete=models.CASCADE, related_name='progress')
            
    date = models.DateField(auto_now_add=True)
    count = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.habit.name} progress on {self.date}"


class FamilyToDoItem(models.Model):
    task_name = models.CharField(max_length=255)
    assigned_to = models.ForeignKey(
         User, on_delete=models.CASCADE, related_name='family_todos', blank=True, null=True)
    due_date = models.DateField()
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.task_name
    

class SamsTodoItem(models.Model):
    task_name = models.CharField(max_length=255)
    assigned_to = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sams_todos')
    due_date = models.DateField()
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.task_name
