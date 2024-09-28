from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views import View
from django.db.models import Q
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
import logging
import os
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic.edit import UpdateView
from .utils import send_fcm_notification

from .models import (Post, PrivateMessage, UserProfile, Habit, FamilyToDoItem,
                     SamsTodoItem, User, HabitProgress)
from .forms import (CustomUserCreationForm, PostForm, PrivateMessageForm,
                    UserProfileForm, SamsTodoForm, HabitForm, FamilyTodoForm)

logger = logging.getLogger(__name__)


def custom_404(request, exception):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)

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

# Custom decorator to restrict actions to staff users


def staff_required(view_func):
    return user_passes_test(lambda u: u.is_staff, login_url='board:message_board')(view_func)


@csrf_exempt
@login_required
def subscribe(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)

    token = request.POST.get('token')
    if not token:
        return JsonResponse({'status': 'error', 'message': 'Token missing'}, status=400)

    try:
        request.user.fcm_token = token  # Assuming 'fcm_token' is a field on the user model
        request.user.save()
    except IntegrityError:
        return JsonResponse({'status': 'error', 'message': 'Database update failed'}, status=500)

    return JsonResponse({'status': 'success'})


class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)
        return redirect('board:welcome')


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user

            # Check if the user has a profile and is a trusted user
            if hasattr(request.user, 'userprofile') and request.user.userprofile.is_trusted_user:
                post.is_moderated = True
            else:
                post.is_moderated = False

            # Check if the content contains any banned words
            if banned_word := contains_banned_words(post.content):
                post.flag_for_moderation(banned_word)
                messages.warning(
                    request, "Your post contains inappropriate content and has been flagged for moderation.")
                return redirect('board:message_board')

            # Use a transaction to ensure atomicity
            with transaction.atomic():
                post.save()
                post.send_creation_notification()

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
    post.delete()  # Directly delete the post instead of using `reject()`
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
            user = form.save(commit=False)
            user.is_approved = False  # Set to False until approved by admin
            user.save()
            messages.info(
                request, 'Your registration is pending approval by the admin.')
            # Redirect to the home page or an info page
            return redirect('board:welcome')
    else:
        form = CustomUserCreationForm()
    return render(request, 'board/register.html', {'form': form})


@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user)
    private_messages = PrivateMessage.objects.filter(
        recipient=user).order_by('-timestamp')
    habits = Habit.objects.filter(user=user)

    total_habits = habits.count()
    completed_habits = habits.filter(completed=True).count()

    # Calculate completion percentage
    if total_habits > 0:
        completion_rate = (completed_habits / total_habits) * 100
    else:
        completion_rate = 0

    flagged_posts = []

    if request.user.is_staff:
        flagged_posts = Post.objects.filter(
            is_flagged=True).order_by('-created_at')

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user.userprofile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your preferences have been updated.')
            return redirect('board:profile', username=user.username)
    else:
        form = UserProfileForm(instance=user.userprofile)

    context = {
        'user_profile': user,
        'posts': posts,
        'private_messages': private_messages,
        'habits': habits,
        'completion_rate': completion_rate,
        'flagged_posts': flagged_posts,
        'is_staff': request.user.is_staff,
        'form': form,
    }

    return render(request, 'board/profile.html', context)



@login_required
def message_board(request):
    posts_list = Post.objects.filter(is_flagged=False).order_by('-created_at')
    paginator = Paginator(posts_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'board/message_board.html', {'page_obj': page_obj})


class UserLoginView(LoginView):
    template_name = 'board/login.html'
    success_url = reverse_lazy('board:message_board')

    def form_valid(self, form):
        user = form.get_user()
        if user.is_approved:
            messages.success(self.request, 'You have successfully logged in.')
            return super().form_valid(form)
        else:
            messages.error(
                self.request, 'Your account is awaiting admin approval.')
            return redirect('board:login')

    def get_success_url(self):
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
    
    for habit in habits:
        habit.reset_if_needed()

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


@login_required
def increment_habit(request, habit_id):
    habit = get_object_or_404(Habit, id=habit_id, user=request.user)

    # Increment the habit count
    habit.increment_count()

    # Log progress
    HabitProgress.objects.create(
        habit=habit, date=datetime.now().date(), count=habit.current_count)

    messages.success(request, f"You've completed {habit.name} {
                     habit.current_count}/{habit.target_count} times!")

    # Redirect back to the user's profile or another page
    return redirect('board:profile', username=request.user.username)


@login_required
def habit_insights(request):
    habits = Habit.objects.filter(user=request.user)
    today = timezone.now().date()

    insights = []

    for habit in habits:
        daily_progress = HabitProgress.objects.filter(
            habit=habit, date=today).aggregate(Sum('count'))['count__sum'] or 0
        weekly_progress = HabitProgress.objects.filter(
            habit=habit, date__gte=today - timedelta(weeks=1)).aggregate(Sum('count'))['count__sum'] or 0
        monthly_progress = HabitProgress.objects.filter(
            habit=habit, date__month=today.month, date__year=today.year).aggregate(Sum('count'))['count__sum'] or 0
        annual_progress = HabitProgress.objects.filter(
            habit=habit, date__year=today.year).aggregate(Sum('count'))['count__sum'] or 0

        # Calculate progress percentage for the daily progress
        if habit.target_count > 0:
            daily_progress_percentage = (
                daily_progress / habit.target_count) * 100
        else:
            daily_progress_percentage = 0

        insights.append({
            'habit': habit,
            'daily_progress': daily_progress,
            'weekly_progress': weekly_progress,
            'monthly_progress': monthly_progress,
            'annual_progress': annual_progress,
            'daily_progress_percentage': daily_progress_percentage
        })

    context = {
        'insights': insights
    }
    return render(request, 'board/habit_insights.html', context)


def is_parent(user):
    return user.is_staff  # or any other condition that defines a parent


@login_required
def family_todo_list(request):
    todos = FamilyToDoItem.objects.filter(
        Q(assigned_to=request.user) | Q(assigned_to__isnull=True)
    )
    return render(request, 'board/family_todo_list.html', {'todos': todos})


@login_required
def add_family_todo(request):
    if request.method == 'POST':
        form = FamilyTodoForm(request.POST)
        if form.is_valid():
            family_todo = form.save(commit=False)
            # Assign the current user if the field is left blank (optional)
            if not family_todo.assigned_to:
                family_todo.assigned_to = None
            family_todo.save()
            return redirect('board:family_todo_list')
    else:
        form = FamilyTodoForm()
    return render(request, 'board/add_family_todo.html', {'form': form})


@login_required
def complete_family_todo(request, todo_id):
    todo = get_object_or_404(FamilyToDoItem, id=todo_id)
    # Ensure that only assigned tasks or tasks for everyone can be marked as complete
    if todo.assigned_to == request.user or todo.assigned_to is None:
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
        private_messages = PrivateMessage.objects.filter(
            recipient=request.user).select_related('sender')
        return render(request, 'board/private_messages.html', {'private_messages': private_messages})

@login_required
def view_message(request):
    private_messages = PrivateMessage.objects.filter(recipient=request.user)
    return render(request, 'board/private_messages.html', {'private_messages': private_messages})


@user_passes_test(lambda u: u.is_superuser)  # Only superusers can approve
def approve_users(request):
    unapproved_users = UserProfile.objects.filter(is_approved=False)

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user_profile = UserProfile.objects.get(id=user_id)
        user_profile.is_approved = True
        user_profile.save()
        messages.success(request, f'User {
                         user_profile.user.username} has been approved.')

    return render(request, 'board/approve_users.html', {'unapproved_users': unapproved_users})


@login_required
def reply_message(request, sender_id):
    sender = get_object_or_404(User, id=sender_id)

    if request.method == 'POST':
        form = PrivateMessageForm(request.POST)
        if form.is_valid():
            private_message = form.save(commit=False)
            private_message.sender = request.user
            private_message.recipient = sender
            private_message.save()
            # Redirect back to the private messages page
            return redirect('board:private_messages')
    else:
        form = PrivateMessageForm()

    return render(request, 'board/reply_message.html', {'form': form, 'sender': sender})
