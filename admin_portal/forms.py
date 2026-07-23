from django import forms
from django.contrib.auth.models import User


class CreateUserForm(forms.Form):
    ROLE_CHOICES = [
        ('field_agent', 'Field agent (can log visits)'),
        ('viewer', 'Viewer (reports only)'),
    ]

    email = forms.EmailField(label="Email")
    password = forms.CharField(
        label="Password",
        min_length=8,
        widget=forms.TextInput(attrs={'placeholder': 'At least 8 characters'}),
        help_text="Set this yourself — no password is generated automatically.",
    )
    role = forms.ChoiceField(label="Role", choices=ROLE_CHOICES, widget=forms.RadioSelect)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
