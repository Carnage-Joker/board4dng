from django import forms
from .models import Post
from .models import PrivateMessage  # Assuming you have a PrivateMessage model
from .models import User  # Ensure this imports your custom user model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User  # Your custom user model


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User  # Use your custom User model
        # Fields to include in the registration form
        fields = ('username', 'email')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User  # Use your custom User model
        # Fields to include in the user change form
        fields = ('username', 'email')


class PrivateMessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.all(), label="Select User")

    class Meta:
        model = PrivateMessage
        fields = ['recipient', 'content']



class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control'}),
        }

