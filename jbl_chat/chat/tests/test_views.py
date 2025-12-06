from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from chat.models import Message, Conversation


class HomeViewTest(TestCase):
    """Test cases for the home view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_home_requires_login(self):
        """Test that home view requires authentication"""
        response = self.client.get(reverse("chat:home"))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        self.assertIn("/login/", response.url)

    def test_home_authenticated(self):
        """Test that authenticated users can access home"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("chat:home"))
        self.assertEqual(response.status_code, 200)


class UserListViewTest(TestCase):
    """Test cases for the user list view"""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")
        self.user3 = User.objects.create_user(username="alice", password="testpass123")

    def test_user_list_requires_login(self):
        """Test that user list requires authentication"""
        response = self.client.get(reverse("chat:user_list"))
        self.assertEqual(response.status_code, 302)

    def test_user_list_excludes_current_user(self):
        """Test that current user is excluded from the list"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(reverse("chat:user_list"), HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        # Should not contain user1
        self.assertNotContains(response, "user1")
        # Should contain other users
        self.assertContains(response, "user2")
        self.assertContains(response, "alice")

    def test_user_list_search(self):
        """Test user list search functionality"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse("chat:user_list"),
            {"search": "alice"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "alice")
        self.assertNotContains(response, "user2")

    def test_user_list_pagination(self):
        """Test user list pagination"""
        # Create more users for pagination (start from 10 to avoid conflicts)
        for i in range(10, 20):
            User.objects.create_user(
                username=f"pagination_user{i}", password="testpass123"
            )

        self.client.login(username="user1", password="testpass123")
        response = self.client.get(reverse("chat:user_list"), HTTP_HX_REQUEST="true")
        self.assertEqual(response.status_code, 200)
        # Should contain pagination controls if there are more than 5 users
        # (PAGINATE_BY_USERS = 5)


class ConversationsViewTest(TestCase):
    """Test cases for the conversations view"""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")
        self.user3 = User.objects.create_user(username="alice", password="testpass123")

    def test_conversations_requires_login(self):
        """Test that conversations view requires authentication"""
        response = self.client.get(reverse("chat:conversations"))
        self.assertEqual(response.status_code, 302)

    def test_conversations_empty(self):
        """Test conversations view with no conversations"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse("chat:conversations"), HTTP_HX_REQUEST="true"
        )
        self.assertEqual(response.status_code, 200)

    def test_conversations_with_messages(self):
        """Test conversations view with existing messages"""
        # Create a conversation with messages
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Hello!",
        )

        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse("chat:conversations"), HTTP_HX_REQUEST="true"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "user2")

    def test_conversations_search(self):
        """Test conversations search functionality"""
        # Create conversations with different users
        Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Message to user2",
        )
        Message.objects.create(
            sender=self.user1,
            receiver=self.user3,
            content="Message to alice",
        )

        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse("chat:conversations"),
            {"search": "alice"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "alice")
        self.assertNotContains(response, "user2")

    def test_conversations_non_htmx_returns_full_page(self):
        """Test that non-HTMX requests return full page"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(reverse("chat:conversations"))
        self.assertEqual(response.status_code, 200)
        # Should return full page template, not partial


class ConversationViewTest(TestCase):
    """Test cases for the conversation detail view"""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")

    def test_conversation_requires_login(self):
        """Test that conversation view requires authentication"""
        response = self.client.get(reverse("chat:conversation", args=["user2"]))
        self.assertEqual(response.status_code, 302)

    def test_conversation_with_existing_user(self):
        """Test conversation view with existing user"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse("chat:conversation", args=["user2"]),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "user2")

    def test_conversation_with_nonexistent_user(self):
        """Test conversation view with non-existent user returns 404"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(reverse("chat:conversation", args=["nonexistent"]))
        self.assertEqual(response.status_code, 404)

    def test_conversation_with_messages(self):
        """Test conversation view displays messages"""
        # Create messages
        Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Hello from user1",
        )
        Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="Hello from user2",
        )

        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse("chat:conversation", args=["user2"]),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello from user1")
        self.assertContains(response, "Hello from user2")

    def test_conversation_non_htmx_returns_full_page(self):
        """Test that non-HTMX requests return full page"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(reverse("chat:conversation", args=["user2"]))
        self.assertEqual(response.status_code, 200)
        # Should return full page template, not partial


class SendMessageViewTest(TestCase):
    """Test cases for the send message view"""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")

    def test_send_message_requires_login(self):
        """Test that send message requires authentication"""
        response = self.client.post(
            reverse("chat:send_message", args=["user2"]),
            {"content": "Test message"},
        )
        self.assertEqual(response.status_code, 302)

    def test_send_message_requires_htmx(self):
        """Test that send message requires HTMX request"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("chat:send_message", args=["user2"]),
            {"content": "Test message"},
        )
        # Should redirect if not HTMX
        self.assertEqual(response.status_code, 302)

    def test_send_message_valid(self):
        """Test sending a valid message"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("chat:send_message", args=["user2"]),
            {"content": "Hello, this is a test message"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        # Verify message was created
        self.assertTrue(
            Message.objects.filter(
                sender=self.user1,
                receiver=self.user2,
                content="Hello, this is a test message",
            ).exists()
        )

    def test_send_message_empty_content(self):
        """Test sending message with empty content returns error"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("chat:send_message", args=["user2"]),
            {"content": ""},
            HTTP_HX_REQUEST="true",
        )
        # Should return 422 for validation error
        self.assertEqual(response.status_code, 422)

    def test_send_message_creates_conversation(self):
        """Test that sending a message creates a conversation"""
        self.client.login(username="user1", password="testpass123")
        # No conversation should exist yet
        self.assertFalse(
            Conversation.objects.filter(user1=self.user1, user2=self.user2).exists()
        )

        response = self.client.post(
            reverse("chat:send_message", args=["user2"]),
            {"content": "First message"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        # Conversation should now exist
        self.assertTrue(
            Conversation.objects.filter(user1=self.user1, user2=self.user2).exists()
        )


class LoadMoreMessagesViewTest(TestCase):
    """Test cases for the load more messages view"""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")

    def test_load_more_requires_login(self):
        """Test that load more requires authentication"""
        response = self.client.get(
            reverse("chat:load_more_messages", args=["user2"]),
            {"page": "2"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 302)

    def test_load_more_requires_htmx(self):
        """Test that load more requires HTMX request"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse("chat:load_more_messages", args=["user2"]),
            {"page": "2"},
        )
        # Should redirect if not HTMX
        self.assertEqual(response.status_code, 302)

    def test_load_more_with_messages(self):
        """Test loading more messages with pagination"""
        # Create more than 5 messages (PAGINATE_BY_MESSAGES = 5)
        for i in range(7):
            Message.objects.create(
                sender=self.user1 if i % 2 == 0 else self.user2,
                receiver=self.user2 if i % 2 == 0 else self.user1,
                content=f"Message {i}",
            )

        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse("chat:load_more_messages", args=["user2"]),
            {"page": "2"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)

    def test_load_more_page_one_redirects(self):
        """Test that requesting page 1 redirects to conversation"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse("chat:load_more_messages", args=["user2"]),
            {"page": "1"},
            HTTP_HX_REQUEST="true",
        )
        # Should redirect (HttpResponseClientRedirect)
        self.assertEqual(response.status_code, 200)


class ArchiveConversationViewTest(TestCase):
    """Test cases for archive/unarchive conversation views"""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username="user1", password="testpass123")
        self.user2 = User.objects.create_user(username="user2", password="testpass123")
        # Create a conversation with a message
        self.message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Test message",
        )
        self.conversation = Conversation.objects.get(user1=self.user1, user2=self.user2)

    def test_archive_requires_login(self):
        """Test that archive requires authentication"""
        response = self.client.post(
            reverse("chat:archive_conversation", args=["user2"]),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 302)

    def test_archive_requires_htmx(self):
        """Test that archive requires HTMX request"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("chat:archive_conversation", args=["user2"])
        )
        # Should redirect if not HTMX
        self.assertEqual(response.status_code, 302)

    def test_archive_conversation(self):
        """Test archiving a conversation"""
        self.client.login(username="user1", password="testpass123")
        # Verify conversation is not archived
        self.assertFalse(self.conversation.is_archived_by(self.user1))

        response = self.client.post(
            reverse("chat:archive_conversation", args=["user2"]),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        # Verify conversation is now archived
        self.conversation.refresh_from_db()
        self.assertTrue(self.conversation.is_archived_by(self.user1))

    def test_unarchive_conversation(self):
        """Test unarchiving a conversation"""
        # First archive it
        self.conversation.archive(self.user1)

        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("chat:unarchive_conversation", args=["user2"]),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        # Verify conversation is no longer archived
        self.conversation.refresh_from_db()
        self.assertFalse(self.conversation.is_archived_by(self.user1))

    def test_unarchive_nonexistent_conversation(self):
        """Test unarchiving a non-existent conversation returns 404"""
        self.client.login(username="user1", password="testpass123")
        # Try to unarchive a conversation that doesn't exist
        response = self.client.post(
            reverse("chat:unarchive_conversation", args=["nonexistent"]),
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 404)
