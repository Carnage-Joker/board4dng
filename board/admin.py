from .models import FamilyToDoItem, SamsTodoItem
from django.contrib import admin
from .models import Post, User, PrivateMessage, UserProfile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


# Customizing the UserAdmin for the custom User model
class CustomUserAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'username', 'is_staff',
                    'is_active', 'is_approved', 'is_trusted_user')
    search_fields = ('email', 'username')
    readonly_fields = ('id', 'date_joined', 'last_login')

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active',
         'is_moderator', 'is_approved', 'is_trusted_user')}),
    )

    # Adding filters for quick access
    list_filter = ('is_staff', 'is_active', 'is_trusted_user',
                   'is_moderator', 'is_approved')


admin.site.register(User, CustomUserAdmin)


# Registering Post model with a decorator
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at']
    search_fields = ['title', 'content']
    # Filtering posts by author and creation date
    list_filter = ['created_at', 'author']


# Registering PrivateMessage model
@admin.register(PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'timestamp']
    search_fields = ['sender__username', 'recipient__username']
    list_filter = ['timestamp']  # Filtering messages by timestamp


# Registering UserProfile model with a decorator
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'profile_visibility',
                    'location_sharing', 'privacy_mode', 'selected_theme']
    search_fields = ['user__username', 'profile_visibility',
                     'location_sharing', 'privacy_mode', 'selected_theme']
    list_filter = ['profile_visibility', 'location_sharing',
                   'privacy_mode', 'selected_theme']

    # board/admin.py


@admin.register(FamilyToDoItem)
class FamilyToDoItemAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'assigned_to', 'due_date', 'completed')
    list_filter = ('completed', 'due_date', 'assigned_to')
    search_fields = ('task_name', 'assigned_to__username')


@admin.register(SamsTodoItem)
class SamsTodoItemAdmin(admin.ModelAdmin):
    list_display = ('task_name', 'assigned_to', 'due_date', 'completed')
    list_filter = ('completed', 'due_date', 'assigned_to')
    search_fields = ('task_name', 'assigned_to__username')
