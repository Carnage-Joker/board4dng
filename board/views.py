from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.contrib import messages
from .forms import PostForm
from .models import Post, send_to_moderator

# Load your banned words list from the file


def load_banned_words(file_path="bad_words.txt"):
    with open(file_path, "r") as file:
        return [line.strip().lower() for line in file.readlines()]


BANNED_WORDS = load_banned_words()


def contains_banned_words(content):
    return any(word in content.lower() for word in BANNED_WORDS)


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
    return render(request, 'board/profile.html', {'user_profile': user, 'posts': posts})


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
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']
            if contains_banned_words(content):
                post = form.save(commit=False)
                messages.info(
                    request, "Your post has been flagged for review. It will be reviewed by a moderator before being published.")
                # Send the post to the moderator for review
                send_to_moderator(post)
                return render(request, 'board/create_post.html', {'form': form})
            else:
                post = form.save(commit=False)
                post.author = request.user
                post.save()
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
            request, "You do not have permission to view this page.")
        return redirect('message_board')

    flagged_posts = Post.objects.filter(is_flagged=True, is_moderated=False)
    return render(request, 'board/moderate_posts.html', {'flagged_posts': flagged_posts})


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
    messages.success(request, "The post has been approved.")
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
