from django.db import models
from django.contrib.auth.models import User


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

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["sender", "receiver", "timestamp"]),
            models.Index(fields=["receiver", "sender", "timestamp"]),
        ]

    def __str__(self):
        return (
            f"{self.sender.username} -> {self.receiver.username}: {self.content[:50]}"
        )
