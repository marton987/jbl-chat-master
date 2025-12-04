from django.views.generic import TemplateView
from django.contrib.auth import mixins
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator

from .forms import UserSearchForm


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

    def get_context_data(self, **kwargs):
        """Get context data for the template"""
        context = super().get_context_data(**kwargs)
        username = kwargs.get("username")
        other_user = get_object_or_404(User, username=username)
        context["other_user"] = other_user
        # TODO: Add messages query in Step 4
        context["messages"] = []
        return context
