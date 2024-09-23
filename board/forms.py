from .models import FamilyToDoItem, SamsTodoItem
from .models import Habit
from django import forms
from .models import Post, UserProfile, User, PrivateMessage, SamsTodoItem, FamilyTodoItem
from django.contrib.auth.forms import UserCreationForm, UserChangeForm


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User  # Use your custom User model
        fields = ('username', 'email', 'password1',
                  'password2')  # Fields for registration


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User  # Use your custom User model
        fields = ('username', 'email')  # Fields for user modification


class PrivateMessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="Select User",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        label="Message"
    )

    class Meta:
        model = PrivateMessage
        fields = ['recipient', 'content']


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Post Title'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Write your post...'}),
        }


class UserProfileForm(forms.ModelForm):
    email_notifications = forms.BooleanField(
        required=False,
        label='Receive Email Notifications',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    privacy_mode = forms.BooleanField(
        required=False,
        label='Enable Privacy Mode',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    selected_theme = forms.ChoiceField(
        choices=UserProfile.selected_theme.field.choices,
        label="Select Theme",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = UserProfile
        fields = ['email_notifications', 'privacy_mode', 'selected_theme',
                  'message_preview', 'auto_logout', 'location_sharing',
                  'profile_visibility']
        widgets = {
            'message_preview': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_logout': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'location_sharing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'profile_visibility': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class HabitForm(forms.ModelForm):
    class Meta:
        model = Habit
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }


# board/forms.py


class FamilyTodoForm(forms.ModelForm):
    class Meta:
        model = FamilyToDoItem
        fields = ['task_name', 'due_date']
        widgets = {
            'task_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter family task'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class SamsTodoForm(forms.ModelForm):
    class Meta:
        model = SamsTodoItem
        fields = ['task_name', 'due_date']
        widgets = {
            'task_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Sam\'s task'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
