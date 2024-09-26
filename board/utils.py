from django.contrib.auth.models import User
import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_to_moderator(post):
    """
    Sends a post to a moderator for review.
    Logs the action and sends an email to the moderator.
    """
    logger.info(f"Post {post.id} flagged for review.")
    try:
        send_mail(
            subject="Post Review Needed",
            message=f"A post with ID {post.id} has been flagged for review. Title: {post.title}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.MODERATOR_EMAIL],
            fail_silently=False,
        )
        logger.info("Email sent to moderator successfully.")
    except Exception as e:
        logger.error(f"Failed to send email to moderator: {e}")


def send_creation_notification(self):
    # Get all users' email addresses
    all_user_emails = User.objects.values_list(
        'email', flat=True).exclude(email='')

    # Send the email to all users
    send_mail(
        subject='New Post Created',
        message=f"A new post has been created by {self.author.username}.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=all_user_emails,
        fail_silently=False,
    )
