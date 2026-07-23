from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.urls import reverse


def user_test_required(test_func, login_url_name='login'):
    """
    Like Django's user_passes_test, but avoids a redirect loop: an
    unauthenticated visitor is sent to the login page (with ?next=...
    as usual), but an authenticated user who simply doesn't have the
    right role gets a 403 instead of being bounced back to login —
    bouncing them to login would just send them straight back here,
    since LoginView.redirect_authenticated_user sends already-logged-in
    users to their 'next' page.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path(), login_url=reverse(login_url_name))
            if not test_func(request.user):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


staff_required = user_test_required(lambda u: u.is_active and u.is_staff)

# Same staff check, but sends unauthenticated visitors to the Admin
# Portal's own login page instead of the regular one.
admin_staff_required = user_test_required(lambda u: u.is_active and u.is_staff, login_url_name='admin_login')
