from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q

from .forms import UserSearchForm, MessageForm
from .models import Message, Conversation


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

    # Get page number from POST data (for pagination) or default to 1
    if request.method == "POST" and request.htmx:
        try:
            page_number = int(request.POST.get("page", 1))
        except (ValueError, TypeError):
            page_number = 1
    else:
        page_number = 1

    paginate_by = 5

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
    page_number = request.GET.get("page", 1)
    paginate_by = 5
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

    # Check if request came from conversation page (archive-form) or chats list
    # django-htmx provides target as the element ID (without #)
    hx_target = getattr(request.htmx, "target", "") if request.htmx else ""
    # Also check the header directly as fallback
    if not hx_target:
        hx_target = request.headers.get("HX-Target", "").lstrip("#")

    if hx_target == "archive-form":
        # Return updated archive button for conversation page
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

    # Check if request came from conversation page (archive-form) or chats list
    # django-htmx provides target as the element ID (without #)
    hx_target = getattr(request.htmx, "target", "") if request.htmx else ""
    # Also check the header directly as fallback
    if not hx_target:
        hx_target = request.headers.get("HX-Target", "").lstrip("#")

    if hx_target == "archive-form":
        # Return updated archive button for conversation page
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
    paginate_by = 2
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
        # If page is 1 or less, redirect to conversation view
        return redirect("chat:conversation", username=username)

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
            messages_html = render(
                request, "chat/partials/_messages.html", context
            ).content.decode("utf-8")
            from django.http import HttpResponse

            return HttpResponse(
                f'<div style="display:none;"></div>'
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
