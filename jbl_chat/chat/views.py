from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.http import HttpResponse, StreamingHttpResponse
from django.db.models import Q
from django.urls import reverse
from django.conf import settings
from django_htmx.http import HttpResponseClientRefresh
from django.utils import timezone
from datetime import timedelta
import time
import json
import re
import logging

from .forms import MessageForm
from .models import Message, Conversation

logger = logging.getLogger(__name__)


@login_required
def home(request):
    """Simple home page - just renders the template"""
    return render(request, "chat/home.html")


@login_required
def user_list(request):
    """Returns the user list partial for HTMX requests"""
    # Get search query from GET (for search form) or POST (for pagination)
    search_query = (
        request.GET.get("search", "").strip() or request.POST.get("search", "").strip()
    )

    # Get page number from request
    page_number = _get_page_number(request)

    paginate_by = settings.PAGINATE_BY_USERS

    # Get all users excluding the current user
    users = User.objects.exclude(id=request.user.id).order_by("username")

    if search_query:
        users = users.filter(username__icontains=search_query)

    # Paginate users
    paginator = Paginator(users, paginate_by)
    page_obj = paginator.get_page(page_number)

    context = {
        "users": page_obj,
        "page_obj": page_obj,
        "paginator": paginator,
        "search_query": search_query,
    }

    return render(request, "chat/partials/_user_list.html", context)


@login_required
def conversations(request):
    """Returns the chats list partial for HTMX requests, full page for non-HTMX requests"""
    # Get search query from GET
    search_query = request.GET.get("search", "").strip()
    page_number = _get_page_number(request)
    paginate_by = settings.PAGINATE_BY_CONVERSATIONS
    current_user = request.user

    # Get all conversations for the current user, ordered by last message timestamp
    conversations = (
        Conversation.get_conversations_for_user(current_user)
        .filter(last_message_timestamp__isnull=False)
        .select_related("user1", "user2")
        .order_by("-last_message_timestamp")
    )

    # Filter by search query if provided
    if search_query:
        # Filter conversations where the other user's username contains the search query
        # Use Q objects to check both user1 and user2 positions
        conversations = conversations.filter(
            Q(user1=current_user, user2__username__icontains=search_query)
            | Q(user2=current_user, user1__username__icontains=search_query)
        )

    # Paginate at database level
    paginator = Paginator(conversations, paginate_by)
    page_obj = paginator.get_page(page_number)

    # Build chat list with other user info
    chats = []
    for conversation in page_obj:
        other_user = conversation.get_other_user(current_user)
        chats.append(
            {
                "user": other_user,
                "latest_timestamp": conversation.last_message_timestamp,
                "last_message": conversation.last_message,
            }
        )

    context = {
        "chats": chats,
        "page_obj": page_obj,
        "paginator": paginator,
        "current_user": current_user,
        "search_query": search_query,
    }

    if request.htmx:
        # Return partial template for HTMX requests
        return render(request, "chat/partials/_chats_list.html", context)
    else:
        # Return full page for non-HTMX requests (direct navigation, page refresh)
        return render(request, "chat/home.html", context)


@login_required
def archive_conversation(request, username):
    """Archive a conversation for the current user."""
    if not request.htmx:
        return redirect("chat:conversation", username=username)

    other_user = get_object_or_404(User, username=username)
    conversation, _ = Conversation.get_or_create_conversation(request.user, other_user)
    conversation.archive(request.user)

    hx_target = request.htmx.target if request.htmx else ""

    if hx_target == "archive-form":
        context = {
            "other_user": other_user,
            "is_archived": conversation.is_archived_by(request.user),
        }
        return render(request, "chat/partials/_archive_button.html", context)
    else:
        # Return updated chats list (for chats list page or default)
        return conversations(request)


@login_required
def unarchive_conversation(request, username):
    """Unarchive a conversation for the current user."""
    if not request.htmx:
        return redirect("chat:conversation", username=username)

    other_user = get_object_or_404(User, username=username)
    conversation = get_object_or_404(
        Conversation,
        (Q(user1=request.user) & Q(user2=other_user))
        | (Q(user1=other_user) & Q(user2=request.user)),
    )
    conversation.unarchive(request.user)

    hx_target = request.htmx.target if request.htmx else ""

    if hx_target == "archive-form":
        context = {
            "other_user": other_user,
            "is_archived": conversation.is_archived_by(request.user),
        }
        return render(request, "chat/partials/_archive_button.html", context)
    else:
        # Return updated chats list (for chats list page or default)
        return conversations(request)


def _get_page_number(request):
    """Extract page number from request"""
    try:
        if request.method == "POST":
            return int(request.POST.get("page", 1))
        return int(request.GET.get("page", 1))
    except (ValueError, TypeError):
        return 1


def _get_queryset(request, other_user):
    """Get messages where current user is sender or receiver with selected user"""
    current_user = request.user
    # Get or create conversation to ensure it exists
    conversation, _ = Conversation.get_or_create_conversation(current_user, other_user)
    # Use conversation to filter messages (more efficient with index)
    return Message.objects.filter(conversation=conversation).order_by(
        "-timestamp"
    )  # Newest first for pagination


def _get_conversation_context(request, other_user, page_number=1):
    """Get context data for the conversation template"""
    # Get or create conversation
    conversation, _ = Conversation.get_or_create_conversation(request.user, other_user)

    # Get paginated messages
    queryset = _get_queryset(request, other_user)
    paginate_by = settings.PAGINATE_BY_MESSAGES
    paginator = Paginator(queryset, paginate_by)
    page_obj = paginator.get_page(page_number)

    # Reverse for display (oldest to newest in chat)
    context = {
        "other_user": other_user,
        "current_user": request.user,
        "conversation": conversation,
        "is_archived": conversation.is_archived_by(request.user),
        "messages": list(page_obj.object_list)[::-1],
        "has_older_messages": page_obj.has_next(),
        "next_page": (page_obj.next_page_number() if page_obj.has_next() else None),
        "message_form": MessageForm(),
    }
    return context


@login_required
def conversation(request, username):
    """View to display conversation between current user and selected user"""
    other_user = get_object_or_404(User, username=username)
    # Always start at page 1 for conversation view - pagination is handled via load_more_messages endpoint
    page_number = 1

    # Get context for the conversation
    context = _get_conversation_context(request, other_user, page_number)

    if request.htmx:
        # Return messages partial for HTMX requests
        return render(request, "chat/partials/_messages.html", context)

    # Return full page for non-HTMX requests
    return render(request, "chat/conversation.html", context)


@login_required
def load_more_messages(request, username):
    """Endpoint to load more messages (pagination) via HTMX"""
    if not request.htmx:
        return redirect("chat:conversation", username=username)

    other_user = get_object_or_404(User, username=username)
    page_number = _get_page_number(request)

    if page_number <= 1:
        return HttpResponseClientRefresh(reverse("chat:conversation", args=[username]))

    context = _get_conversation_context(request, other_user, page_number)
    return render(request, "chat/partials/_load_more_messages.html", context)


@login_required
def send_message(request, username):
    """Endpoint to send a message via HTMX"""
    if not request.htmx:
        return redirect("chat:conversation", username=username)

    other_user = get_object_or_404(User, username=username)
    form = MessageForm(request.POST)

    if form.is_valid():
        # Create the message
        message = Message.objects.create(
            sender=request.user,
            receiver=other_user,
            content=form.cleaned_data["content"],
        )

        # Check if this is the first message
        queryset = _get_queryset(request, other_user)
        total_messages = queryset.count()

        if total_messages == 1:
            # First message - need to replace the entire message-list to show messages-container
            # Use out-of-band swap to replace #message-list with full messages
            context = {
                "messages": [message],
                "current_user": request.user,
                "other_user": other_user,
                "has_older_messages": False,
                "next_page": None,
            }
            # Use render_to_string for cleaner out-of-band swap
            messages_html = render_to_string(
                "chat/partials/_messages.html", context, request=request
            )

            # Return out-of-band swap response
            return HttpResponse(
                f'<div id="message-list" hx-swap-oob="innerHTML">{messages_html}</div>'
            )
        else:
            # Subsequent messages - return single message to append
            context = {
                "message": message,
                "current_user": request.user,
            }
            return render(request, "chat/partials/_single_message.html", context)

    # Form validation failed - return form with errors
    context = {
        "other_user": other_user,
        "current_user": request.user,
        "message_form": form,
    }
    return render(request, "chat/partials/_message_form.html", context, status=422)


# ============================================================================
# SSE Streaming Helper Functions
# ============================================================================


def _is_sse_request(request):
    """Check if the request is for Server-Sent Events (SSE)"""
    accept_header = request.META.get("HTTP_ACCEPT", "")
    return request.htmx or "text/event-stream" in accept_header


def _get_initial_timestamp(conversation):
    """Get the initial timestamp to start streaming from"""
    last_message = (
        Message.objects.filter(conversation=conversation).order_by("-timestamp").first()
    )
    if last_message:
        # Use timestamp minus 1 second to avoid missing messages created in the same second
        return last_message.timestamp - timedelta(seconds=1)
    else:
        # No messages yet - start from a year ago to catch any existing messages
        return timezone.now() - timedelta(days=365)


def _clean_html_for_sse(html):
    """Clean HTML for SSE format by removing newlines and extra whitespace"""
    # Remove newlines and carriage returns
    cleaned = html.replace("\n", " ").replace("\r", "").strip()
    # Collapse multiple spaces into single space
    return re.sub(r"\s+", " ", cleaned)


def _render_message_for_sse(message, current_user, request):
    """Render a message as HTML for SSE streaming"""
    context = {
        "message": message,
        "current_user": current_user,
    }
    html = render_to_string(
        "chat/partials/_single_message.html", context, request=request
    )
    return _clean_html_for_sse(html)


def _create_keepalive_event():
    """Create a keepalive SSE event to prevent connection timeout"""
    html = '<div id="sse-keepalive" style="display:none;"></div>'
    return f"event: keepalive\ndata: {html}\n\n"


def _create_error_event(error_message, is_fatal=False):
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
    cleaned_html = _clean_html_for_sse(error_html)
    return f"event: message\ndata: {cleaned_html}\n\n"


def _get_new_messages(conversation, last_timestamp, current_user):
    """Query for new messages since the last timestamp, excluding current user's messages"""
    return (
        Message.objects.filter(conversation=conversation, timestamp__gt=last_timestamp)
        .exclude(sender=current_user)  # Don't stream own messages (handled by form)
        .order_by("timestamp")
        .select_related("sender", "receiver")
    )


def _create_sse_response(event_stream):
    """Create a StreamingHttpResponse with proper SSE headers"""
    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"  # Disable buffering for nginx
    return response


@login_required
def stream_messages(request, username):
    """SSE endpoint to stream new messages for a conversation"""
    # Redirect non-SSE requests to the conversation page
    if not _is_sse_request(request):
        return redirect("chat:conversation", username=username)

    other_user = get_object_or_404(User, username=username)
    current_user = request.user
    conversation, _ = Conversation.get_or_create_conversation(current_user, other_user)
    last_timestamp = _get_initial_timestamp(conversation)

    def event_stream():
        """Generator function that yields SSE events"""
        nonlocal last_timestamp

        try:
            # Send initial keepalive to establish connection
            yield _create_keepalive_event()

            poll_count = 0
            while True:
                # Check if client disconnected
                if hasattr(request, "_closed") and request._closed:
                    break

                try:
                    # Get new messages since last check
                    new_messages = _get_new_messages(
                        conversation, last_timestamp, current_user
                    )

                    # Stream each new message in order
                    last_message_in_batch = None
                    for message in new_messages:
                        message_html = _render_message_for_sse(
                            message, current_user, request
                        )
                        yield f"event: message\ndata: {message_html}\n\n"
                        last_message_in_batch = message

                    # Update timestamp after processing all messages in this batch
                    # Use the latest message's timestamp plus a small buffer to avoid
                    # missing messages created at the exact same timestamp
                    if last_message_in_batch:
                        last_timestamp = last_message_in_batch.timestamp + timedelta(
                            microseconds=1
                        )

                    # Send keepalive every 30 seconds to prevent timeout
                    poll_count += 1
                    if poll_count % 30 == 0:
                        yield _create_keepalive_event()

                except Exception as e:
                    # Non-fatal error - log and continue streaming
                    logger.error(f"Error in SSE stream: {str(e)}", exc_info=True)
                    yield _create_error_event(
                        f"Connection issue: {str(e)}", is_fatal=False
                    )

                # Poll every 1 second
                time.sleep(1)

        except GeneratorExit:
            # Client disconnected - this is normal
            pass
        except Exception as e:
            # Fatal error - log and send error event
            logger.error(f"Fatal error in SSE stream: {str(e)}", exc_info=True)
            yield _create_error_event(str(e), is_fatal=True)

    return _create_sse_response(event_stream)
