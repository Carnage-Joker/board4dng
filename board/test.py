from django.core import mail
from django.test import TestCase
from .models import Post
from .utils import send_to_moderator


class SendToModeratorTestCase(TestCase):
    def test_send_to_moderator(self):
        """
        Test sending a post to a moderator sends an email.
        """
        # Setup: Create a dummy post instance (not saved to db)
        post = Post(title="Test Post", content="This is a test post.")

        # Ensure the outbox is empty initially
        self.assertEqual(len(mail.outbox), 0)

        # Call the function under test
        send_to_moderator(post)

        # Check that one message has been sent
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the subject of the first message is correct
        self.assertEqual(mail.outbox[0].subject, 'Post Review Needed')
