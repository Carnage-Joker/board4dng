


import logging
from django.core.mail import send_mail
from django.conf import settings

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
