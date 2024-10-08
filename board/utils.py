import logging
import requests
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_to_moderator(post, reason=None):
    """Notify moderators about a flagged post with a specific reason."""
    moderator_email = settings.MODERATOR_EMAIL
    if not moderator_email:
        logger.error("Moderator email is not set in settings.")
        return

    message = f"A post has been flagged for moderation.\nReason: {
        reason}\n\nPost Content:\n{post.content}"

    try:
        send_mail(
            subject="Post Flagged for Moderation",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[moderator_email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Failed to send moderation email: {e}")


def send_fcm_notification(fcm_token, sender_username):
    """Send FCM notification to user with specified token."""
    url = 'https://fcm.googleapis.com/fcm/send'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'key={settings.FCM_SERVER_KEY}'
    }
    payload = {
        'to': fcm_token,
        'notification': {
            'title': 'New Private Message',
            'body': f'You have a new message from {sender_username}',
        },
        'data': {
            'message': 'You have a new private message.'
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"FCM Notification failed: {e}")
        return None
