from django.core.mail import send_mail
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, PrivateMessageForm, CustomUserCreationForm
from .models import Post, PrivateMessage, User
from .utils import send_to_moderator

# Load your banned words list from the file


def load_banned_words(file_path=None):
    if not file_path:
        # Set default file path if none is provided
        file_path = os.path.join(settings.BASE_DIR, 'board', 'bad_words.txt')

    with open(file_path, "r") as file:
        # Read the file line by line and strip any extra whitespace
        return [word.strip().lower() for word in file.readlines()]


BANNED_WORDS = load_banned_words()


def contains_banned_words(content):
    # Check if any banned word is found in the content
    for word in BANNED_WORDS:
        if word in content.lower():
            return word
    return None


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
                # Send notification to moderators
                send_to_moderator(post)
                messages.warning(request, f"Your post contains inappropriate content: '{banned_word}'. It has been flagged for moderation.")
                return redirect('message_board')

            if request.user.is_staff or request.user.profile.is_trusted_user:
                post.is_moderated = True
            else:
                post.is_flagged = False
                post.is_moderated = True

            post.save()

            # Notify moderators or others
            send_mail(
                subject='New Post Created',
                message=f"A new post has been created by {post.author.username}.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.MODERATOR_EMAIL],
                fail_silently=False,
            )
            messages.success(request, "Your post has been successfully published!")
            return redirect('message_board')
    else:
        form = PostForm()
    return render(request, 'board/create_post.html', {'form': form})


@login_required
def moderate_posts(request):
    if not request.user.is_staff:
        messages.error(
            request, "You do not have permission to moderate posts.")
        return redirect('message_board')

    # Get all flagged posts for moderation
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
        return redirect('moderate_posts')

    post.is_moderated = True
    post.is_flagged = False
    post.save()
    messages.success(request, "The post has been approved and is now visible.")
    return redirect('moderate_posts')


@login_required
def reject_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if not request.user.is_staff:
        messages.error(
            request, "You do not have permission to reject this post.")
        return redirect('moderate_posts')

    post.delete()
    messages.success(request, "The post has been rejected and deleted.")
    return redirect('moderate_posts')


def welcome(request):
    return render(request, 'board/welcome.html')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Registration successful. Please log in.")
            return redirect('login')
        else:
            messages.error(
                request, "There was an error with your registration.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'board/register.html', {'form': form})


def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user)
    private_messages = PrivateMessage.objects.filter(
        sender=user)  # Adjust this query as needed
    if request.user.is_staff:
        flagged_posts = Post.objects.filter(
            is_flagged=True).order_by('-created_at')
    else:
        flagged_posts = []

    context = {
        'flagged_posts': flagged_posts,
        'is_staff': request.user.is_staff,
        'user_profile': user,
        'posts': posts,
        'private_messages': private_messages,
    }
    return render(request, 'board/profile.html', context)


@login_required
def message_board(request):
    # Filter to get only posts that are not flagged and order them by 'created_at'
    posts_list = Post.objects.filter(is_flagged=False).order_by('created_at')
    paginator = Paginator(posts_list, 5)  # Show 5 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'board/message_board.html', context)


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('message_board')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'board/login.html')


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('message_board')
    else:
        form = PostForm(instance=post)
    return render(request, 'board/edit_post.html', {'form': form})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        post.delete()
        return redirect('message_board')
    return render(request, 'board/delete_post.html', {'post': post})


@login_required
def create_message(request):
    if request.method == 'POST':
        form = PrivateMessageForm(request.POST)
        if form.is_valid():
            private_message = form.save(commit=False)
            private_message.sender = request.user
            private_message.save()

            # Send email notification
            send_mail(
                subject='New Private Message',
                message=f"You have a new private message from {
                    private_message.sender.username}.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                # Assuming PrivateMessage model has a receiver field.
                recipient_list=[private_message.receiver.email],
                fail_silently=False,
            )

            messages.success(request, 'Your message has been sent!')
            return redirect('message_board')
        else:
            messages.error(
                request, 'There was an error sending your message. Please try again.')
    else:
        form = PrivateMessageForm()

    return render(request, 'board/create_message.html', {'form': form})


def flag_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.is_flagged = True
    post.save()
    messages.info(request, "The post has been flagged for review.")
    return redirect('message_board')


def edit_message(request, message_id):
    message = get_object_or_404(PrivateMessage, id=message_id)
    if request.method == 'POST':
        form = PrivateMessageForm(request.POST, instance=message)
        if form.is_valid():
            form.save()
            return redirect('message_board')
    else:
        form = PrivateMessageForm(instance=message)
    return render(request, 'board/edit_message.html', {'form': form})


def delete_message(request, message_id):
    message = get_object_or_404(PrivateMessage, id=message_id)
    if request.method == 'POST':
        message.delete()
        return redirect('message_board')
    return render(request, 'board/delete_message.html', {'message': message})
# ...


@login_required
def view_private_messages(request):
    messages_list = PrivateMessage.objects.filter(
        receiver=request.user).order_by('-created_at')
    paginator = Paginator(messages_list, 10)  # Show 10 messages per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'board/private_messages.html', {'page_obj': page_obj})
