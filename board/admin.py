from django.contrib import admin
from .models import Post, User
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
<<<<<<< HEAD
    list_display = ['email', 'username', 'is_staff', 'is_active']
=======
    list_display = ['email', 'username', 'is_staff']
>>>>>>> abc58840565bea23e3a5fa530a64db1130824f99



@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at']
    search_fields = ['title', 'content']

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_moderator']
    search_fields = ['username', 'email']
