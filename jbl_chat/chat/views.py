from django.views.generic import TemplateView
from django.contrib.auth import mixins
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q

from .forms import UserSearchForm, MessageForm
from .models import Message


class HomeView(mixins.LoginRequiredMixin, TemplateView):
    """Home page - displays list of all users (excluding current user) with HTMX support"""

    template_name = "chat/home.html"
    partial_template = "chat/partials/_user_list.html"
    paginate_by = 5

    def get_queryset(self):
        """Get all users excluding the current user"""
        search_query = self.request.GET.get("search", "").strip()
        users = User.objects.exclude(id=self.request.user.id).order_by("username")

        if search_query:
            users = users.filter(username__icontains=search_query)

        return users

    def get_context_data(self, **kwargs):
        """Get context data for the template"""
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get("search", "").strip()
        page_number = self.request.GET.get("page", 1)

        # Get paginated users
        users = self.get_queryset()
        paginator = Paginator(users, self.paginate_by)
        page_obj = paginator.get_page(page_number)

        context["users"] = page_obj
        context["page_obj"] = page_obj
        context["paginator"] = paginator
        context["form"] = UserSearchForm(initial={"search": search_query})
        context["search_query"] = search_query
        return context

    def get(self, request, *args, **kwargs):
        """Handle GET requests with HTMX support"""
        context = self.get_context_data()

        # If it's an HTMX request, return the partial template
        if request.htmx:
            return render(request, self.partial_template, context)

        # Otherwise, return the full page template
        return render(request, self.template_name, context)


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
        return Message.objects.filter(
            (Q(sender=current_user) & Q(receiver=other_user))
            | (Q(sender=other_user) & Q(receiver=current_user))
        ).order_by(
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

        # Get paginated messages
        queryset = self.get_queryset(other_user)
        paginator = Paginator(queryset, self.paginate_by)
        page_obj = paginator.get_page(page_number)

        # Reverse for display (oldest to newest in chat)
        context.update(
            {
                "other_user": other_user,
                "current_user": self.request.user,
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
