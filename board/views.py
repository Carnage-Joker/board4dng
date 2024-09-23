from django.contrib.auth.decorators import login_required, user_passes_test
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
import logging
import os
from django.views.decorators.csrf import csrf_exempt
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic.edit import UpdateView
from .models import Post, PrivateMessage, UserProfile, Habit, FamilyToDoItem, SamsTodoItem, User
from .forms import (CustomUserCreationForm, PostForm, PrivateMessageForm,
                    UserProfileForm, SamsTodoForm, HabitForm, FamilyTodoForm)
from .utils import send_to_moderator

logger = logging.getLogger(__name__)

# Decorator to restrict actions to staff users


def staff_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(
                request, "You do not have permission for this action.")
            return redirect('board:message_board')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def load_banned_words(file_path=None):
    if not file_path:
        file_path = os.path.join(settings.BASE_DIR, 'board', 'bad_words.txt')

    try:
        with open(file_path, "r") as file:
            return [word.strip().lower() for word in file.readlines()]
    except FileNotFoundError:
        logger.error("Banned words file not found.")
        return []


BANNED_WORDS = load_banned_words()


def contains_banned_words(content):
    for word in BANNED_WORDS:
        if word in content.lower():
            return word
    return None


@csrf_exempt
@login_required
def subscribe(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

    token = request.POST.get('token')
    if not token:
        return JsonResponse({'status': 'error', 'message': 'Token missing'}, status=400)

    User.objects.filter(id=request.user.id).update(fcm_token=token)
    return JsonResponse({'status': 'success'})


class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        return redirect('board:login')

    
@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']
            post = form.save(commit=False)
            post.author = request.user

            banned_word = contains_banned_words(content)
            if banned_word:
                post.is_flagged = True
                post.is_moderated = False
                post.save()
                send_to_moderator(post)
                messages.warning(request, f"Your post contains inappropriate content: '{
                                  banned_word}'. It has been flagged for moderation.")
                return redirect('board:message_board')

            post.is_moderated = True if request.user.is_staff or request.user.profile.is_trusted_user else False
            post.save()

            send_mail(
                subject='New Post Created',
                message=f"A new post has been created by {
                    post.author.username}.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.MODERATOR_EMAIL],
                fail_silently=False,
            )
            messages.success(
                request, "Your post has been successfully published!")
            return redirect('board:message_board')
    else:
        form = PostForm()

    return render(request, 'board/create_post.html', {'form': form})


@staff_required
def moderate_posts(request):
    flagged_posts = Post.objects.filter(is_flagged=True, is_moderated=False)
    paginator = Paginator(flagged_posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'board/moderate_posts.html', {'page_obj': page_obj})


@staff_required
def approve_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.is_moderated = True
    post.is_flagged = False
    post.save()
    messages.success(request, "The post has been approved and is now visible.")
    return redirect('board:moderate_posts')


@staff_required
def reject_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.delete()
    messages.success(request, "The post has been rejected and deleted.")
    return redirect('board:moderate_posts')


def welcome(request):
    return render(request, 'board/welcome.html', {'firebase_config': settings.FIREBASE_CONFIG})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Registration successful. Please log in.")
            return redirect('board:login')
        else:
            messages.error(
                request, "There was an error with your registration.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'board/register.html', {'form': form})


@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user)
    private_messages = PrivateMessage.objects.filter(sender=user)

    flagged_posts = []
    if request.user.is_staff:
        flagged_posts = Post.objects.filter(
            is_flagged=True).order_by('-created_at')

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your preferences have been updated.')
            return redirect('board:profile', username=user.username)
    else:
        form = UserProfileForm(instance=user)

    context = {
        'flagged_posts': flagged_posts,
        'is_staff': request.user.is_staff,
        'user_profile': user,
        'posts': posts,
        'private_messages': private_messages,
        'form': form,
    }
    return render(request, 'board/profile.html', context)


@login_required
def message_board(request):
    posts_list = Post.objects.filter(is_flagged=False).order_by('created_at')
    paginator = Paginator(posts_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'board/message_board.html', {'page_obj': page_obj})


class UserLoginView(LoginView):
    template_name = 'board/login.html'
    success_url = reverse_lazy('board:message_board')
    
    def get_success_url(self):
        return self.success_url


def user_logout(request):
    logout(request)
    return redirect('board:welcome')


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('board:message_board')
    else:
        form = PostForm(instance=post)

    return render(request, 'board/edit_post.html', {'form': form})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        post.delete()
        return redirect('board:message_board')

    return render(request, 'board/delete_post.html', {'post': post})


@login_required
def create_message(request):
    if request.method == 'POST':
        form = PrivateMessageForm(request.POST)
        if form.is_valid():
            private_message = form.save(commit=False)
            private_message.sender = request.user
            private_message.save()

            recipient = private_message.recipient

            if recipient.email_notifications:
                send_mail(
                    subject='New Private Message',
                    message=f"You have a new private message from {
                        private_message.sender.username}.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient.email],
                    fail_silently=False,
                )

            if recipient.fcm_token:
                send_fcm_notification(
                    recipient.fcm_token, private_message.sender.username)

            messages.success(request, 'Your message has been sent!')
            return redirect('board:message_board')
        else:
            messages.error(
                request, 'There was an error sending your message. Please try again.')
    else:
        form = PrivateMessageForm()

    return render(request, 'board/create_message.html', {'form': form})


def send_fcm_notification(fcm_token, sender_username):
    url = 'https://fcm.googleapis.com/fcm/send'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'key={settings.FCM_SERVER_KEY}'
    }
    payload = {
        'to': fcm_token,
        'notification': {
            'title': 'New Private Message',
            'body': f'You have a new message from {sender_username}',
        },
        'data': {
            'message': 'You have a new private message.'
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"FCM notification failed: {response.content}")
        return {'error': response.content}


@login_required
def flag_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.is_flagged = True
    post.save()
    messages.info(request, "The post has been flagged for review.")
    return redirect('board:message_board')


@login_required
def edit_message(request, message_id):
    message = get_object_or_404(PrivateMessage, id=message_id)
    if request.method == 'POST':
        form = PrivateMessageForm(request.POST, instance=message)
        if form.is_valid():
            form.save()
            return redirect('board:message_board')
    else:
        form = PrivateMessageForm(instance=message)

    return render(request, 'board/edit_message.html', {'form': form})


@login_required
def delete_message(request, message_id):
    message = get_object_or_404(PrivateMessage, id=message_id)
    if request.method == 'POST':
        message.delete()
        return redirect('board:message_board')

    return render(request, 'board/delete_message.html', {'message': message})


@login_required
def view_private_messages(request):
    messages_list = PrivateMessage.objects.filter(
        receiver=request.user).order_by('-created_at')
    paginator = Paginator(messages_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'board/private_messages.html', {'page_obj': page_obj})


class ProfileSettingsView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'board/profile_settings.html'

    def get_success_url(self):
        return reverse('board:profile', kwargs={'username': self.request.user.username})

    def form_valid(self, form):
        messages.success(self.request, 'Your settings have been updated.')
        return super().form_valid(form)

    def get_object(self, queryset=None):
        try:
            return self.request.user.userprofile
        except UserProfile.DoesNotExist:
            return UserProfile.objects.create(user=self.request.user)


@login_required
def habit_tracker(request):
    habits = Habit.objects.filter(user=request.user)
    return render(request, 'habit_tracker.html', {'habits': habits})


@login_required
def add_habit(request):
    if request.method == 'POST':
        form = HabitForm(request.POST)
        if form.is_valid():
            habit = form.save(commit=False)
            habit.user = request.user
            habit.save()
            return redirect('habit_tracker')
    else:
        form = HabitForm()
    return render(request, 'add_habit.html', {'form': form})


@login_required
def mark_habit_complete(request, habit_id):
    habit = Habit.objects.get(id=habit_id, user=request.user)
    habit.completed = True
    habit.save()
    return redirect('habit_tracker')


# board/views.py


# ---------------------
# Family To-Do Views
# ---------------------
# board/views.py

def is_parent(user):
    return user.is_staff  # or any other condition that defines a parent


@login_required
@user_passes_test(is_parent)
def sams_todo_list(request):
    sams_todos = SamsTodoItem.objects.filter(assigned_to=request.user)
    return render(request, 'board/sams_todo_list.html', {'sams_todos': sams_todos})



@login_required
def family_todo_list(request):
    todos = FamilyToDoItem.objects.filter(assigned_to=request.user)
    return render(request, 'board/family_todo_list.html', {'todos': todos})


@login_required
def add_family_todo(request):
    if request.method == 'POST':
        form = FamilyTodoForm(request.POST)
        if form.is_valid():
            family_todo = form.save(commit=False)
            family_todo.assigned_to = request.user
            family_todo.save()
            return redirect('family_todo_list')
    else:
        form = FamilyTodoForm()
    return render(request, 'board/add_family_todo.html', {'form': form})


@login_required
def complete_family_todo(request, todo_id):
    todo = get_object_or_404(FamilyToDoItem, id=todo_id,
                             assigned_to=request.user)
    todo.completed = True
    todo.save()
    return redirect('family_todo_list')

# ---------------------
# Sam's To-Do Views
# ---------------------


@login_required
def add_sams_todo(request):
    if request.method == 'POST':
        form = SamsTodoForm(request.POST)
        if form.is_valid():
            sams_todo = form.save(commit=False)
            sams_todo.assigned_to = request.user
            sams_todo.save()
            return redirect('sams_todo_list')
    else:
        form = SamsTodoForm()
    return render(request, 'board/add_sams_todo.html', {'form': form})


@login_required
@user_passes_test(is_parent)
def complete_sams_todo(request, todo_id):
    sams_todo = get_object_or_404(
        SamsTodoItem, id=todo_id, assigned_to=request.user)
    sams_todo.completed = True
    sams_todo.save();
    return redirect('board:sams_todo_list')
