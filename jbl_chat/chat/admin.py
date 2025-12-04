from django.contrib import admin
from .models import Message, Conversation


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = [
        "user1",
        "user2",
        "last_message_preview",
        "last_message_timestamp",
        "archived_count",
    ]
    list_filter = ["last_message_timestamp", "updated_at"]
    search_fields = [
        "user1__username",
        "user2__username",
        "last_message__content",
    ]
    readonly_fields = ["last_message_timestamp", "updated_at"]
    filter_horizontal = ["archived_by"]
    date_hierarchy = "last_message_timestamp"

    def last_message_preview(self, obj):
        """Display a preview of the last message content."""
        if obj.last_message:
            return (
                obj.last_message.content[:100] + "..."
                if len(obj.last_message.content) > 100
                else obj.last_message.content
            )
        return "No messages"

    last_message_preview.short_description = "Last Message"

    def archived_count(self, obj):
        """Display the number of users who archived this conversation."""
        return obj.archived_by.count()

    archived_count.short_description = "Archived By"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = [
        "sender",
        "receiver",
        "content_preview",
        "timestamp",
        "conversation",
    ]
    list_filter = ["timestamp", "sender", "receiver", "conversation"]
    search_fields = ["content", "sender__username", "receiver__username"]
    readonly_fields = ["timestamp"]
    date_hierarchy = "timestamp"

    def content_preview(self, obj):
        """Display a preview of the message content."""
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    content_preview.short_description = "Content"
