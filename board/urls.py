# This code snippet is defining URL patterns for a Django web application. In Django, URL patterns are
# defined in the `urlpatterns` list within a Django app's `urls.py` file. Each URL pattern is
# associated with a specific view function that will be called when a user accesses that particular
# URL.
from django.urls import path
from . import views
from .views import ProfileSettingsView
from django.contrib.auth import views as auth_views

app_name = 'board'

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('register/', views.register, name='register'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('messageboard/', views.message_board, name='message_board'),
    path('edit/<int:post_id>/', views.edit_post, name='edit_post'),
    path('delete/<int:post_id>/', views.delete_post, name='delete_post'),
    path('moderate/', views.moderate_posts, name='moderate_posts'),
    path('approve/<int:post_id>/', views.approve_post, name='approve_post'),
    path('reject/<int:post_id>/', views.reject_post, name='reject_post'),
    path('flag/<int:post_id>/', views.flag_post, name='flag_post'),
    path('create_message/', views.create_message, name='create_message'),
    path('create_post/', views.create_post, name='create_post'),
    path('edit_message/<int:message_id>/',
         views.edit_message, name='edit_message'),
    path('delete_message/<int:message_id>/',
         views.delete_message, name='delete_message'),
    path('profile/<str:username>/settings/', ProfileSettingsView.as_view(), name='profile_settings'),
    path('password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='board/password_reset.html'),
         name='password_reset'),

    path('password_reset_done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='board/password_reset_done.html'),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='board/password_reset_confirm.html'),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='board/password_reset_complete.html'),
         name='password_reset_complete'),
    ]
