from django.views.generic import TemplateView
from django.contrib.auth import mixins


class HomeView(mixins.LoginRequiredMixin, TemplateView):
    """Home page with HTMX test interactions"""

    template_name = "chat/home.html"
