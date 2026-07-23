from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy

from .forms import EmailAuthenticationForm


class CustomLoginView(LoginView):
    """
    The Field Agent login (mounted at /field/login/). Authenticates by
    email against accounts.backends.EmailBackend, but rejects accounts
    that only have report ViewerAccess (and aren't also staff) — those
    are management accounts and belong on the Management login instead.
    Staff can still use this page too, e.g. to log a visit themselves.
    """
    template_name = 'registration/login.html'
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_staff and hasattr(user, 'viewer_access'):
            form.add_error(None, "This is a management account — please use the Management login instead.")
            return self.form_invalid(form)
        auth_login(self.request, user)
        return redirect(self.get_success_url())


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')
