from django.views.generic import TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin


class HomeView(LoginRequiredMixin, TemplateView):
    """Home page with HTMX test interactions"""

    template_name = "chat/home.html"


class CustomLoginView(LoginView):
    """Custom login view"""

    template_name = "chat/login.html"
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    """Custom logout view"""

    pass
