from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
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
]
