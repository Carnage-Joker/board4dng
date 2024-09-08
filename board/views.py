
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, PrivateMessageForm
from .models import Post, PrivateMessage
from .utils import send_to_moderator

# Load your banned words list from the file


def load_banned_words(file_path="bad_words.txt"):
    with open(file_path, "r") as file:
        return [line.strip().lower() for line in file.readlines()]


BANNED_WORDS = load_banned_words()


def contains_banned_words(content):
    return any(word in content.lower() for word in BANNED_WORDS)

def welcome(request):
    return render(request, 'board/welcome.html')
    
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('message_board')
        else:
            messages.error(
                request, "Registration failed. Please correct the error below.")
    else:
        form = UserCreationForm()
    return render(request, 'board/register.html', {'form': form})


def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user)
    private_messages = PrivateMessage.objects.filter(
        sender=user)  # Adjust this query as needed
    context = {
        'user_profile': user,
        'posts': posts,
        'private_messages': private_messages,
    }
    return render(request, 'board/profile.html', context)



@login_required
def message_board(request):
    posts_list = Post.objects.all().order_by('-created_at')
    paginator = Paginator(posts_list, 5)  # Show 5 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'posts': posts_list
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
            messages.success(request, 'Your message has been sent!')
            # Redirect to your message board or another relevant page
            return redirect('message_board')
        else:
            messages.error(
                request, 'There was an error sending your message. Please try again.')
    else:
        form = PrivateMessageForm()

    return render(request, 'board/create_message.html', {'form': form})


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']
            post = form.save(commit=False)
            post.author = request.user

            if contains_banned_words(content):
                # Flag the post for review
                post.is_flagged = True
                post.save()

                # Notify the moderator
                send_to_moderator(post)

                messages.info(
                    request, "Your post has been flagged for review. It will be reviewed by a moderator before being published.")
                return redirect('message_board')
            else:
                # No banned words, post directly
                post.is_flagged = False
                post.is_moderated = True
                post.save()
                messages.success(request, "Your post has been published!")
                return redirect('message_board')

    else:
        form = PostForm()

    return render(request, 'board/create_post.html', {'form': form})


def flag_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.is_flagged = True
    post.save()
    messages.info(request, "The post has been flagged for review.")
    return redirect('message_board')


@login_required
def moderate_posts(request):
    if not request.user.is_staff:
        messages.error(
            request, "You do not have permission to moderate posts.")
        return redirect('message_board')

    # Get all flagged posts that are not yet moderated
    flagged_posts = Post.objects.filter(is_flagged=True, is_moderated=False)

    return render(request, 'board/moderate_posts.html', {'flagged_posts': flagged_posts})


@login_required
def approve_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if not request.user.is_staff:
        messages.error(
            request, "You do not have permission to approve this post.")
        return redirect('moderate_posts')

    # Approve the post
    post.is_moderated = True
    post.is_flagged = False
    post.save()
    messages.success(
        request, "The post has been approved and is now visible to everyone.")
    return redirect('moderate_posts')


@login_required
def reject_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if not request.user.is_staff:
        messages.error(
            request, "You do not have permission to reject this post.")
        return redirect('moderate_posts')

    # Delete the post
    post.delete()
    messages.success(request, "The post has been rejected and deleted.")
    return redirect('moderate_posts')


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