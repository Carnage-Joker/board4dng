from django import forms
from .models import Post, UserProfile, User, PrivateMessage
from django.contrib.auth.forms import UserCreationForm, UserChangeForm


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User  # Use your custom User model
        # Fields to include in the registration form
        fields = ('username', 'email', 'password1', 'password2')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User  # Use your custom User model
        # Fields to include in the user change form
        fields = ('username', 'email')


class PrivateMessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.all(), label="Select User")
    content = forms.CharField(widget=forms.Textarea)

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


class UserProfileForm(forms.ModelForm):
    email_notifications = forms.BooleanField(
        required=False, label='Receive Email Notifications')

    class Meta:
        model = UserProfile
        fields = ['email_notifications', 'privacy_mode', 'selected_theme',
                  'message_preview', 'auto_logout', 'location_sharing',
                  'profile_visibility']




