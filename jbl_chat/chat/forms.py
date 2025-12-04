from django import forms


class UserSearchForm(forms.Form):
    """Form for searching/filtering users in the user list."""

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Search users...",
            }
        ),
    )

