from django import forms


class HierarchyUploadForm(forms.Form):
    file = forms.FileField(
        label="Hierarchy Excel file (.xlsx)",
        help_text="Expected headers: FR ID, Region, BU, FR Status, FR City, "
                   "FR Address, ARM Name, ARM Emp #, Email",
    )

    def clean_file(self):
        uploaded = self.cleaned_data['file']
        if not uploaded.name.lower().endswith('.xlsx'):
            raise forms.ValidationError("Please upload a .xlsx file.")
        return uploaded


class SetPasswordForm(forms.Form):
    new_password = forms.CharField(
        label="New password",
        min_length=8,
        widget=forms.TextInput(attrs={'placeholder': 'At least 8 characters'}),
    )
