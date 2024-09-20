from django.contrib import admin
from .models import Post, User, PrivateMessage, UserProfile
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


class CustomUserAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'username', 'is_staff', 'is_active', 'is_approved', 'is_trusted_user')
    search_fields = ('email', 'username')
    readonly_fields = ('id', 'date_joined', 'last_login')
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_moderator', 'is_approved', 'is_trusted_user')}),
    )


admin.site.register(User, CustomUserAdmin)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at']
    search_fields = ['title', 'content']


class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'timestamp']
    search_fields = ['sender', 'recipient']
    
    
admin.site.register(PrivateMessage, PrivateMessageAdmin)


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'profile_visibility',
                    'location_sharing', 'privacy_mode', 'selected_theme']
    search_fields = ['user', 'profile_visibility', 'location_sharing', 'privacy_mode', 'selected_theme']
    

admin.site.register(UserProfile, UserProfileAdmin)
