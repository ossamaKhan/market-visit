from django import forms
from django.contrib.auth.forms import AuthenticationForm


class EmailAuthenticationForm(AuthenticationForm):
    """
    Same as Django's AuthenticationForm, but presents/validates the
    identifier field as an email address. The field is still internally
    named 'username' (that's what AuthenticationForm.clean() passes to
    authenticate()), but it's relabeled, and validated as an email.
    """
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'autofocus': True}),
    )
