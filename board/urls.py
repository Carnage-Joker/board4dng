# This code snippet is defining URL patterns for a Django web application. In Django, URL patterns are
# defined in the `urlpatterns` list within a Django app's `urls.py` file. Each URL pattern is
# associated with a specific view function that will be called when a user accesses that particular
# URL.
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .views import ProfileSettingsView, UserLoginView, LogoutView, PrivateMessageView

app_name = 'board'

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('register/', views.register, name='register'),
    path('subscribe/', views.subscribe, name='subscribe'),
    # Family To-Do URLs
    path('family_todo/', views.family_todo_list, name='family_todo_list'),
    path('family_todo/add/', views.add_family_todo, name='add_family_todo'),
    path('family_todo/complete/<int:todo_id>/',
         views.complete_family_todo, name='complete_family_todo'),
    #  Habit URLs
    path('habit/', views.habit_tracker, name='habit_tracker'),
    path('habit/add/', views.add_habit, name='add_habit'),
    path('habit/complete/<int:habit_id>/',
         views.mark_habit_complete, name='complete_habit'),
    path('increment_habit/<int:habit_id>/',
         views.increment_habit, name='increment_habit'),
    path('profile/<str:username>/', views.profile, name='profile'),


    # Sam's To-Do URLs
    path('sams_todo/', views.sams_todo_list, name='sams_todo_list'),
    path('sams_todo/add/', views.add_sams_todo, name='add_sams_todo'),
    path('sams_todo/complete/<int:todo_id>/',
         views.complete_sams_todo, name='complete_sams_todo'),

    # Authentication URLs
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('messageboard/', views.message_board, name='message_board'),
    path('edit/<int:post_id>/', views.edit_post, name='edit_post'),
    path('delete/<int:post_id>/', views.delete_post, name='delete_post'),
    path('moderate/', views.moderate_posts, name='moderate_posts'),
    path('approve/<int:post_id>/', views.approve_post, name='approve_post'),
    path('reject/<int:post_id>/', views.reject_post, name='reject_post'),
    path('flag/<int:post_id>/', views.flag_post, name='flag_post'),
    path('create_message/', views.create_message, name='create_message'),
    path('reply_message/<int:sender_id>/',
         views.reply_message, name='reply_message'),
    path('view_message/<int:message_id>/',
         views.view_message, name='view_message'),
    path('create_post/', views.create_post, name='create_post'),
    path('edit_message/<int:message_id>/',
         views.edit_message, name='edit_message'),
    path('delete_message/<int:message_id>/',
         views.delete_message, name='delete_message'),
    path('private_messages/', PrivateMessageView.as_view(),
         name='private_messages'),
    path('profile/<str:username>/settings/',
         ProfileSettingsView.as_view(), name='profile_settings'),
    path('password_reset/', auth_views.PasswordResetView.as_view(),
         name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(),
         name='password_reset_complete'),
    ]
