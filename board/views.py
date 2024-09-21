import requests
from django.urls import reverse
from .forms import UserProfileForm
from .models import UserProfile
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
import requests
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CustomUserCreationForm, PostForm, PrivateMessageForm, UserProfileForm
from .models import Post, PrivateMessage, User
from .utils import send_to_moderator


def load_banned_words(file_path=None):
    if not file_path:
        file_path = os.path.join(settings.BASE_DIR, 'board', 'bad_words.txt')

    with open(file_path, "r") as file:
        return [word.strip().lower() for word in file.readlines()]


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
        return JsonResponse(
            {'status': 'error', 'message': 'Invalid request method'},
            status=400
        )

    token = request.POST.get('token')
    if not token:
        return JsonResponse(
            {'status': 'error', 'message': 'Token missing'},
            status=400
        )

    User.objects.filter(id=request.user.id).update(fcm_token=token)
    return JsonResponse({'status': 'success'})


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
                messages.warning(
                    request, f"Your post contains inappropriate content: '{
                        banned_word}'. It has been flagged for moderation."
                )
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


@login_required
def moderate_posts(request):
    if not request.user.is_staff:
        messages.error(
            request, "You do not have permission to moderate posts.")
        return redirect('board:message_board')

    flagged_posts = Post.objects.filter(is_flagged=True, is_moderated=False)
    paginator = Paginator(flagged_posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'board/moderate_posts.html', {'page_obj': page_obj})


@login_required
def approve_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if not request.user.is_staff:
        messages.error(
            request, "You do not have permission to approve this post.")
        return redirect('board:moderate_posts')

    post.is_moderated = True
    post.is_flagged = False
    post.save()
    messages.success(request, "The post has been approved and is now visible.")
    return redirect('board:moderate_posts')


@login_required
def reject_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if not request.user.is_staff:
        messages.error(
            request, "You do not have permission to reject this post.")
        return redirect('board:moderate_posts')

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

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your preferences have been updated.')
            return redirect('board:profile', username=user.username)
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'board/profile.html', {'form': form, 'user_profile': user})


@login_required
def message_board(request):
    posts_list = Post.objects.filter(is_flagged=False).order_by('created_at')
    paginator = Paginator(posts_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'board/message_board.html', {'page_obj': page_obj})


@csrf_protect
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip().lower()
        password = request.POST.get('password')

        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('board:message_board')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Both username and password are required.")

    return render(request, 'board/login.html')


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

            # Check if the recipient wants email notifications
            if recipient.email_notifications:
                send_mail(
                    subject='New Private Message',
                    message=f"You have a new private message from {
                        private_message.sender.username}.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient.email],
                    fail_silently=False,
                )

            # Send Push Notification if FCM token exists
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
        'Authorization': f'key={settings.FCM_SERVER_KEY}'  # FCM Server Key
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
        # Log the error or take other actions if the notification fails
        return {'error': response.content}


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
        # Redirect to the profile page after successful form submission
        return reverse('board:profile', kwargs={'username': self.request.user.username})

    def form_valid(self, form):
        # Optionally add a success message
        messages.success(self.request, 'Your settings have been updated.')
        return super().form_valid(form)
    
    def get_object(self, queryset=None):
        try:
            return self.request.user.userprofile
        except UserProfile.DoesNotExist:
            # Create the user profile if it doesn't exist
            return UserProfile.objects.create(user=self.request.user)
