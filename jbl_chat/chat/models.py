from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q


class Conversation(models.Model):
    """Model representing a conversation between two users."""

    user1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="conversations_as_user1",
        db_index=True,
    )
    user2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="conversations_as_user2",
        db_index=True,
    )
    last_message = models.ForeignKey(
        "Message",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversation_last_message",
    )
    last_message_timestamp = models.DateTimeField(null=True, blank=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    archived_by = models.ManyToManyField(
        User,
        related_name="archived_conversations",
        blank=True,
        help_text="Users who have archived this conversation",
    )

    class Meta:
        ordering = ["-last_message_timestamp"]
        indexes = [
            models.Index(fields=["user1", "last_message_timestamp"]),
            models.Index(fields=["user2", "last_message_timestamp"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user1", "user2"], name="unique_conversation_pair"
            ),
        ]

    def __str__(self):
        return f"Conversation: {self.user1.username} <-> {self.user2.username}"

    def get_other_user(self, user):
        """Get the other user in the conversation."""
        if user == self.user1:
            return self.user2
        return self.user1

    @classmethod
    def get_or_create_conversation(cls, user1, user2):
        """Get or create a conversation between two users.
        Ensures user1.id < user2.id to maintain consistency.
        """
        # Ensure consistent ordering (user1.id < user2.id)
        if user1.id > user2.id:
            user1, user2 = user2, user1
        conversation, created = cls.objects.get_or_create(user1=user1, user2=user2)
        return conversation, created

    def is_archived_by(self, user):
        """Check if this conversation is archived by the given user."""
        return self.archived_by.filter(id=user.id).exists()

    def archive(self, user):
        """Archive this conversation for the given user."""
        if not self.is_archived_by(user):
            self.archived_by.add(user)

    def unarchive(self, user):
        """Unarchive this conversation for the given user."""
        self.archived_by.remove(user)

    @classmethod
    def get_conversations_for_user(cls, user, include_archived=False):
        """Get all conversations for a given user.

        Args:
            user: The user to get conversations for
            include_archived: If True, include archived conversations. Default False.
        """
        queryset = cls.objects.filter(Q(user1=user) | Q(user2=user)).select_related(
            "user1", "user2", "last_message__sender", "last_message__receiver"
        )
        if not include_archived:
            queryset = queryset.exclude(archived_by=user)
        return queryset


class Message(models.Model):
    """Model representing a message between two users."""

    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages", db_index=True
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages", db_index=True
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["sender", "receiver", "timestamp"]),
            models.Index(fields=["receiver", "sender", "timestamp"]),
            models.Index(fields=["conversation", "timestamp"]),
        ]

    def __str__(self):
        return (
            f"{self.sender.username} -> {self.receiver.username}: {self.content[:50]}"
        )

    def save(self, *args, **kwargs):
        """Override save to automatically create/update conversation."""
        # Get or create conversation
        conversation, _ = Conversation.get_or_create_conversation(
            self.sender, self.receiver
        )
        self.conversation = conversation

        # Save the message first so it has a primary key
        super().save(*args, **kwargs)

        # Update conversation's last message (now that message is saved)
        conversation.last_message = self
        conversation.last_message_timestamp = self.timestamp
        conversation.save(update_fields=["last_message", "last_message_timestamp"])
