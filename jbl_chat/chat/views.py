from django.contrib.auth.decorators import login_required
from django.contrib.auth import mixins
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.generic import TemplateView

from .forms import UserSearchForm, MessageForm
from .models import Message, Conversation


@login_required
def home(request):
    """Simple home page - just renders the template"""
    return render(request, "chat/home.html")


@login_required
def user_list(request):
    """Returns the user list partial for HTMX requests"""
    search_query = request.GET.get("search", "").strip()
    page_number = request.GET.get("page", 1)
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
    """Returns the chats list partial for HTMX requests - shows users with conversations"""
    page_number = request.GET.get("page", 1)
    paginate_by = 5
    current_user = request.user

    # Get all conversations for the current user, ordered by last message timestamp
    conversations = (
        Conversation.get_conversations_for_user(current_user)
        .filter(last_message_timestamp__isnull=False)
        .order_by("-last_message_timestamp")
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
    }

    return render(request, "chat/partials/_chats_list.html", context)


@login_required
def archive_conversation(request, username):
    """Archive a conversation for the current user."""
    if not request.htmx:
        return render(request, "chat/home.html")

    other_user = get_object_or_404(User, username=username)
    conversation, _ = Conversation.get_or_create_conversation(request.user, other_user)
    conversation.archive(request.user)

    # Check if request came from conversation page or chats list
    hx_target = request.headers.get("HX-Target", "")
    if "chats-list" in hx_target or not hx_target:
        # Return updated chats list
        return conversations(request)
    else:
        # Return success response (button will update via HTMX)
        from django.http import HttpResponse

        return HttpResponse(status=204)  # No Content - HTMX will handle UI update


@login_required
def unarchive_conversation(request, username):
    """Unarchive a conversation for the current user."""
    if not request.htmx:
        return render(request, "chat/home.html")

    other_user = get_object_or_404(User, username=username)
    conversation = get_object_or_404(
        Conversation,
        (Q(user1=request.user) & Q(user2=other_user))
        | (Q(user1=other_user) & Q(user2=request.user)),
    )
    conversation.unarchive(request.user)

    # Check if request came from conversation page or chats list
    hx_target = request.headers.get("HX-Target", "")
    if "chats-list" in hx_target or not hx_target:
        # Return updated chats list
        return conversations(request)
    else:
        # Return success response (button will update via HTMX)
        from django.http import HttpResponse

        return HttpResponse(status=204)  # No Content - HTMX will handle UI update


class ConversationView(mixins.LoginRequiredMixin, TemplateView):
    """View to display conversation between current user and selected user"""

    template_name = "chat/conversation.html"
    partial_template = "chat/partials/_messages.html"
    load_more_partial = "chat/partials/_load_more_messages.html"
    button_partial = "chat/partials/_load_more_button.html"
    paginate_by = 2

    def get_queryset(self, other_user):
        """Get messages where current user is sender or receiver with selected user"""
        current_user = self.request.user
        # Get or create conversation to ensure it exists
        conversation, _ = Conversation.get_or_create_conversation(
            current_user, other_user
        )
        # Use conversation to filter messages (more efficient with index)
        return Message.objects.filter(conversation=conversation).order_by(
            "-timestamp"
        )  # Newest first for pagination

    def _get_page_number(self, request):
        """Extract page number from request"""
        try:
            if request.method == "POST":
                return int(request.POST.get("page", 1))
            return int(request.GET.get("page", 1))
        except (ValueError, TypeError):
            return 1

    def get_context_data(self, page_number=1, other_user=None, **kwargs):
        """Get context data for the template"""
        context = super().get_context_data(**kwargs)
        if other_user is None:
            username = kwargs.get("username")
            other_user = get_object_or_404(User, username=username)

        # Get or create conversation
        conversation, _ = Conversation.get_or_create_conversation(
            self.request.user, other_user
        )

        # Get paginated messages
        queryset = self.get_queryset(other_user)
        paginator = Paginator(queryset, self.paginate_by)
        page_obj = paginator.get_page(page_number)

        # Reverse for display (oldest to newest in chat)
        context.update(
            {
                "other_user": other_user,
                "current_user": self.request.user,
                "conversation": conversation,
                "is_archived": conversation.is_archived_by(self.request.user),
                "messages": list(page_obj.object_list)[::-1],
                "has_older_messages": page_obj.has_next(),
                "next_page": (
                    page_obj.next_page_number() if page_obj.has_next() else None
                ),
                "message_form": MessageForm(),
            }
        )
        return context

    def get(self, request, *args, **kwargs):
        """Handle GET requests"""
        page_number = self._get_page_number(request)
        context = self.get_context_data(page_number=page_number, **kwargs)

        if request.htmx:
            template = (
                self.load_more_partial if page_number > 1 else self.partial_template
            )
            return render(request, template, context)

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """Handle POST requests for load-more and send-message"""
        if not request.htmx:
            return self.get(request, *args, **kwargs)

        username = kwargs.get("username")
        other_user = get_object_or_404(User, username=username)

        # Check if this is a message form submission (has 'content' field)
        if "content" in request.POST:
            return self._handle_send_message(request, other_user)

        # Otherwise, it's a load-more request
        return self._handle_load_more(request, other_user)

    def _handle_load_more(self, request, other_user):
        """Handle load-more pagination requests"""
        page_number = self._get_page_number(request)
        context = self.get_context_data(page_number=page_number, other_user=other_user)
        template = self.load_more_partial if page_number > 1 else self.partial_template
        return render(request, template, context)

    def _handle_send_message(self, request, other_user):
        """Handle message sending requests"""
        form = MessageForm(request.POST)

        if form.is_valid():
            # Create the message
            Message.objects.create(
                sender=request.user,
                receiver=other_user,
                content=form.cleaned_data["content"],
            )

            # Get the latest messages (most recent page)
            queryset = self.get_queryset(other_user)
            paginator = Paginator(queryset, self.paginate_by)
            page_obj = paginator.get_page(1)  # Get first page (newest messages)

            context = {
                "other_user": other_user,
                "current_user": request.user,
                "messages": list(page_obj.object_list)[::-1],  # Reverse for display
                "has_older_messages": page_obj.has_next(),
                "next_page": (
                    page_obj.next_page_number() if page_obj.has_next() else None
                ),
                "message_form": MessageForm(),  # Reset form
            }

            # Return updated messages
            return render(
                request,
                "chat/partials/_messages.html",
                context,
            )

        # Form validation failed - return form with errors
        context = {
            "other_user": other_user,
            "current_user": request.user,
            "message_form": form,
        }
        return render(request, "chat/partials/_message_form.html", context, status=422)
