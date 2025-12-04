from django.contrib.auth import login, views
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django_htmx.http import HttpResponseClientRedirect


class CustomLoginView(views.LoginView):
    """Custom login view with HTMX support"""

    template_name = "core/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        """Handle valid form submission with HTMX support"""
        # Perform the login (this is what super().form_valid() does)
        login(self.request, form.get_user())
        redirect_to = self.get_success_url()

        # If it's an HTMX request, use HttpResponseClientRedirect
        if self.request.htmx:
            return HttpResponseClientRedirect(redirect_to)

        # Otherwise, return a normal redirect
        return HttpResponseRedirect(redirect_to)

    def form_invalid(self, form):
        """Handle invalid form submission with HTMX support"""
        messages.error(
            self.request, "Your username and password didn't match. Please try again."
        )
        if self.request.htmx:
            context = self.get_context_data(form=form)
            return render(self.request, "core/partials/_login_form.html", context)
        return super().form_invalid(form)


class CustomLogoutView(views.LogoutView):
    """Custom logout view with HTMX support"""

    def post(self, request, *args, **kwargs):
        """Handle logout with HTMX support"""
        # Call the parent's post method to perform logout
        response = super().post(request, *args, **kwargs)

        # If it's an HTMX request, use HttpResponseClientRedirect for full page reload
        if request.htmx:
            return HttpResponseClientRedirect(self.get_success_url())

        return response
