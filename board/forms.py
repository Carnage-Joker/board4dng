from django import forms
from .models import Post
from .models import PrivateMessage  # Assuming you have a PrivateMessage model
from .models import User  # Ensure this imports your custom user model


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

