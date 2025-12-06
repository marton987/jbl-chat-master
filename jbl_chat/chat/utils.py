import re
import time
import logging
from datetime import timedelta
from django.utils import timezone
from django.http import StreamingHttpResponse
from django.template.loader import render_to_string
from .models import Message

logger = logging.getLogger(__name__)


def get_page_number(request):
    """Extract page number from request"""
    try:
        if request.method == "POST":
            return int(request.POST.get("page", 1))
        return int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        return 1


# ============================================================================
# SSE Streaming Helper Functions
# ============================================================================


def is_sse_request(request):
    """Check if the request is for Server-Sent Events (SSE)"""
    accept_header = request.META.get("HTTP_ACCEPT", "")
    return request.htmx or "text/event-stream" in accept_header


def get_initial_timestamp(conversation):
    """Get the initial timestamp to start streaming from"""
    last_message = (
        Message.objects.filter(conversation=conversation).order_by("-timestamp").first()
    )
    if last_message:
        # Use timestamp plus a small buffer to start AFTER the most recent message
        # This prevents re-streaming messages that are already displayed on page load
        return last_message.timestamp + timedelta(microseconds=1)
    else:
        # No messages yet - start from a year ago to catch any existing messages
        return timezone.now() - timedelta(days=365)


def clean_html_for_sse(html):
    """Clean HTML for SSE format by removing newlines and extra whitespace"""
    # Remove newlines and carriage returns
    cleaned = html.replace("\n", " ").replace("\r", "").strip()
    # Collapse multiple spaces into single space
    return re.sub(r"\s+", " ", cleaned)


def render_message_for_sse(message, current_user, request):
    """Render a message as HTML for SSE streaming"""
    context = {
        "message": message,
        "current_user": current_user,
    }
    html = render_to_string(
        "chat/partials/_single_message.html", context, request=request
    )
    return clean_html_for_sse(html)


def create_keepalive_event():
    """Create a keepalive SSE event to prevent connection timeout"""
    html = '<div id="sse-keepalive" style="display:none;"></div>'
    return f"event: keepalive\ndata: {html}\n\n"


def create_error_event(error_message, is_fatal=False):
    """Create an error SSE event"""
    alert_class = "alert-danger" if is_fatal else "alert-warning"
    fade_class = "alert-dismissible fade show" if not is_fatal else ""
    close_button = (
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>'
        if not is_fatal
        else ""
    )
    error_html = (
        f'<div class="alert {alert_class} {fade_class}" role="alert">'
        f"{'<strong>Connection Error:</strong> ' if is_fatal else '<small>'}"
        f"{error_message}"
        f"{'</small>' if not is_fatal else ''}"
        f"{close_button}"
        f"</div>"
    )
    cleaned_html = clean_html_for_sse(error_html)
    return f"event: message\ndata: {cleaned_html}\n\n"


def get_new_messages(conversation, last_timestamp, current_user):
    """Query for new messages since the last timestamp, excluding current user's messages"""
    return (
        Message.objects.filter(conversation=conversation, timestamp__gt=last_timestamp)
        .exclude(sender=current_user)  # Don't stream own messages (handled by form)
        .order_by("timestamp")
        .select_related("sender", "receiver")
    )


def create_sse_response(event_stream):
    """Create a StreamingHttpResponse with proper SSE headers"""
    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  # Disable buffering for nginx
    return response
