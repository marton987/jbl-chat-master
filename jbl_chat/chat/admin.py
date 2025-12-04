from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["sender", "receiver", "content_preview", "timestamp"]
    list_filter = ["timestamp", "sender", "receiver"]
    search_fields = ["content", "sender__username", "receiver__username"]
    readonly_fields = ["timestamp"]
    date_hierarchy = "timestamp"

    def content_preview(self, obj):
        """Display a preview of the message content."""
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    content_preview.short_description = "Content"
