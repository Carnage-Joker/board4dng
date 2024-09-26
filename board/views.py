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
from .utils import send_to_moderator, send_creation_notification

logger = logging.getLogger(__name__)


# Custom decorator to restrict actions to staff users
def staff_required(view_func):
    return user_passes_test(lambda u: u.is_staff, login_url='board:message_board')(view_func)


# Load banned words from a file
def load_banned_words(file_path=None):
    if not file_path:
        file_path = os.path.join(settings.BASE_DIR, 'board', 'bad_words.txt')

    try:
        with open(file_path, "r") as file:
            words = [word.strip().lower() for word in file.readlines()]
            logger.info("Banned words loaded successfully.")
            return words
    except FileNotFoundError:
        logger.error("Banned words file not found.")
        return []


BANNED_WORDS = load_banned_words()


def contains_banned_words(content):
    content_lower = content.lower()
    return next((word for word in BANNED_WORDS if word in content_lower), None)


@csrf_exempt
@login_required
def subscribe(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

    token = request.POST.get('token')
    if not token:
        return JsonResponse({'status': 'error', 'message': 'Token missing'}, status=400)

    try:
        request.user.update(fcm_token=token)
    except IntegrityError:
        return JsonResponse({'status': 'error', 'message': 'Database update failed'}, status=500)

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
            post = form.save(commit=False)
            post.author = request.user

            banned_word = contains_banned_words(post.content)
            if banned_word:
                post.flag_for_moderation(banned_word)
                messages.warning(request, f"Your post contains inappropriate content: '{banned_word}'. It has been flagged for moderation.")
                return redirect('board:message_board')

            post.is_moderated = request.user.is_staff or request.user.profile.is_trusted_user
            post.save()

            post.send_creation_notification()
            messages.success(request, "Your post has been successfully published!")
            return redirect('board:message_board')
            else:
            form = PostForm()

            return render(request, 'board/create_post.html', {'form': form})
        else:
        return render(request, 'board/create_post.html', {'form': PostForm()})
    else:
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
    post.reject()  # Refactored into the Post model
    messages.success(request, "The post has been rejected and deleted.")
    return redirect('board:moderate_posts')


def welcome(request):
    context = {
        'firebase_config': settings.FIREBASE_CONFIG,
        'is_authenticated': request.user.is_authenticated
    }
    return render(request, 'board/welcome.html', context)


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
    fail_silently = False

    def get_success_url(self):
        messages.success(self.request, 'You have successfully logged in.')
        return self.success_url


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your post has been updated.')
            return redirect('board:message_board')
    else:
        form = PostForm(instance=post)
        messages.error(request, 'There was an error updating the post. Please try again.')
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

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"FCM Notification failed: {e}")
        return None


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
            messages.success(request, 'Your message has been updated.')
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
    return render(request, 'board/habit_tracker.html', {'habits': habits})


@login_required
def add_habit(request):
    if request.method == 'POST':
        form = HabitForm(request.POST)
        if form.is_valid():
            habit = form.save(commit=False)
            habit.user = request.user
            habit.save()
            messages.success(request, 'Habit added successfully!')
            return redirect('board:habit_tracker')
    else:
        form = HabitForm()
        messages.error(request, 'There was an error adding the habit. Check you filled everything in correctly.')
    return render(request, 'board/add_habit.html', {'form': form})


@login_required
def mark_habit_complete(request, habit_id):
    habit = Habit.objects.get(id=habit_id, user=request.user)
    habit.completed = True
    habit.save()
    messages.success(request, 'Good job! Keep up the good work!')
    return redirect('board:habit_tracker')


# Check if user is a parent
def is_parent(user):
    return user.is_staff  # or any other condition that defines a parent


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
            return redirect('board:family_todo_list')
    else:
        form = FamilyTodoForm()
    return render(request, 'board/add_family_todo.html', {'form': form})


@login_required
def complete_family_todo(request, todo_id):
    todo = get_object_or_404(FamilyToDoItem, id=todo_id,
                             assigned_to=request.user)
    todo.completed = True
    todo.save()
    return redirect('board:family_todo_list')


@login_required
@user_passes_test(is_parent)
def sams_todo_list(request):
    # Fetch the user Mick (you can also fetch by ID if needed)
    mick = get_object_or_404(User, username="Mick")

    # Filter Sam's tasks for Mick
    sams_todos = SamsTodoItem.objects.filter(assigned_to=mick)

    return render(request, 'board/sams_todo_list.html', {'sams_todos': sams_todos})


@login_required
@user_passes_test(is_parent)
def add_sams_todo(request):
    # Ensure tasks are always assigned to Mick
    mick = get_object_or_404(User, username="Mick")

    if request.method == 'POST':
        form = SamsTodoForm(request.POST)
        if form.is_valid():
            sams_todo = form.save(commit=False)
            sams_todo.assigned_to = mick  # Assigning to Mick explicitly
            sams_todo.save()
            return redirect('board:sams_todo_list')
    else:
        form = SamsTodoForm()

    return render(request, 'board/add_sams_todo.html', {'form': form})


@login_required
@user_passes_test(is_parent)
def complete_sams_todo(request, todo_id):
    sams_todo = get_object_or_404(
        SamsTodoItem, id=todo_id, assigned_to=request.user)
    sams_todo.completed = True
    sams_todo.save()
    return redirect('board:sams_todo_list')


class PrivateMessageView(LoginRequiredMixin, View):
    def get(self, request):
        # Fetch messages for the currently logged-in user
        private_messages = PrivateMessage.objects.filter(
            recipient=request.user)

        if sender := request.GET.get('sender'):
            private_messages = private_messages.filter(
                sender__username=sender)
        return render(request, 'board/private_messages.html', {'private_messages': private_messages})

