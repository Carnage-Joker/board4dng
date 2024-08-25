from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import Post
from .forms import PostForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.models import User


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('message_board')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


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
        'form': PostForm(),  # Assuming you have a PostForm for adding posts
    }
    return render(request, 'message_board.html', context)



# User login view
def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
    return render(request, 'board/login.html')

# User logout view

def user_logout(request):
    logout(request)
    return redirect('login')


def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = PostForm(instance=post)
    return render(request, 'board/edit_post.html', {'form': form})


def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        post.delete()
        return redirect('index')
    return render(request, 'board/delete_post.html', {'post': post})