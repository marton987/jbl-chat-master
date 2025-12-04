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


class MessageForm(forms.Form):
    """Form for sending messages."""

    content = forms.CharField(
        max_length=1000,
        required=True,
        widget=forms.Textarea(
            attrs={
                "class": "form-control border-0 shadow-none p-0",
                "placeholder": "Type your message...",
                "rows": 3,
                "style": "resize: none;",
            }
        ),
    )
