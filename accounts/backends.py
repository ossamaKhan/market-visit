from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Authenticates against the user's email address instead of username.
    The login form still posts its field as 'username' (Django's
    AuthenticationForm convention) — here that value is simply expected
    to contain an email address, and we look the user up by email.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        try:
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            user = User.objects.filter(email__iexact=username).order_by('id').first()

        if user is not None and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
