from django.shortcuts import render, redirect, get_object_or_404
from blogs.models import Blog, Category
from django.contrib.auth.decorators import login_required,  user_passes_test
from . forms import BlogPostForm, CategoryForm, AddUserForm, EditUserForm
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from accounts.models import Profile
from django.contrib import messages
from .email_utils import send_newsletter_email
import logging
import uuid
from datetime import datetime
from django.core.cache import cache
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)

# Create your views here.
def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

def user_list(request):
    users = User.objects.select_related("profile").all()
    return render(request, "your_template.html", {"users": users})

@login_required(login_url='login')
@user_passes_test(is_admin_user)
def dashboard(request):
    category_count = Category.objects.all().count()
    blogs_count = Blog.objects.all().count()
    profile, _ = Profile.objects.get_or_create(user=request.user)
    users_count = User.objects.all().count()
    
    context = {
        'category_count': category_count,
        'blogs_count': blogs_count,
        'profile': profile,
        'users_count': users_count,
    }
    return render(request, 'dashboard/dashboard.html', context)

@login_required
@user_passes_test(is_admin_user)
def categories(request):
    categories = Category.objects.all().order_by('-created_at')
    context = {
        'categories': categories
    }
    return render(request, 'dashboard/categories.html', context)

@login_required
@user_passes_test(is_admin_user)
@never_cache  # Never cache this view
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category_name = form.cleaned_data['category_name']
            category.slug = slugify(category_name) + ''+str(category.id if category.id else '')
            category.save()
            return redirect('categories')
    form = CategoryForm()
    context = {
        'form': form,
    }
    return render(request, 'dashboard/add_category.html', context)

def edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save(commit=False)
            category_name = form.cleaned_data['category_name']
            category.slug = slugify(category_name) + ''+str(category.id)
            category.save()
            return redirect('categories')
    form = CategoryForm(instance=category)
    context = {
        'form': form,
        'category': category
    }
    return render(request, 'dashboard/edit_category.html', context)

@login_required
@user_passes_test(is_admin_user)
@never_cache  # Never cache this view
def delete_category(request, pk):
    try:
        category = get_object_or_404(Category, pk=pk)
        category_name = category.category_name
        
        # Check if category has associated posts
        posts_count = Blog.objects.filter(category=category).count()
        
        if posts_count > 0:
            messages.warning(request, f'Cannot delete category "{category_name}" - it has {posts_count} associated posts. Please reassign or delete the posts first.')
        else:
            category.delete()
            
            # Clear cache after successful deletion
            cache.clear()  # Clear all cache
            # Or clear specific cache keys:
            # cache.delete_many([f'categories_list', f'category_{pk}'])
            
            messages.success(request, f'Category "{category_name}" has been deleted successfully.')
            logger.info(f'Category deleted: {category_name} by user {request.user.username}')
        
    except Exception as e:
        messages.error(request, f'Error deleting category: {str(e)}')
        logger.error(f'Error deleting category {pk}: {e}')
    
    return redirect('categories')


def posts(request):
    posts = Blog.objects.all()
    context = {
        'posts': posts,
    }
    return render(request, 'dashboard/posts.html', context)

def generate_unique_slug(title, post_id=None, existing_slugs=None):
    """
    Generate a unique slug for a blog post.
    
    Args:
        title: The post title
        post_id: The post ID (if available)
        existing_slugs: Set of existing slugs to avoid (optional)
    
    Returns:
        A unique slug string
    """
    base_slug = slugify(title)
    
    if post_id:
        # If we have a post ID, use it
        slug = f"{base_slug}-{post_id}"
    else:
        # If no post ID yet, create a temporary unique identifier
        timestamp = int(datetime.now().timestamp())
        slug = f"{base_slug}-{timestamp}"
    
    # Double-check uniqueness against database
    counter = 1
    original_slug = slug
    while Blog.objects.filter(slug=slug).exists():
        slug = f"{original_slug}-{counter}"
        counter += 1
    
    return slug

@login_required
@user_passes_test(is_admin_user)
@never_cache  # Never cache this view
def add_post(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            
            title = form.cleaned_data['title']
            
            # Generate initial slug without ID (will be updated after save)
            post.slug = generate_unique_slug(title)
            
            # Save the post first to get an ID
            post.save()
            
            # CRITICAL: Save many-to-many relationships (TAGS!)
            form.save_m2m()
            
            # Now update slug with the actual ID
            final_slug = generate_unique_slug(title, post.id)
            if post.slug != final_slug:
                post.slug = final_slug
                post.save(update_fields=['slug'])
            
            # Check if the post is being published
            is_published = getattr(post, 'status', 'Draft') == 'Published'
            
            if is_published:
                try:
                    # Send newsletter to all subscribers
                    send_newsletter_email(post)
                    messages.success(request, f'Post "{post.title}" has been published and newsletter sent to subscribers!')
                    logger.info(f'Newsletter sent for post: {post.title}')
                except Exception as e:
                    messages.warning(request, f'Post published successfully, but failed to send newsletter: {str(e)}')
                    logger.error(f'Failed to send newsletter for post {post.title}: {e}')
            else:
                messages.success(request, f'Post "{post.title}" has been saved as {post.status}.')
            
            return redirect('posts')
        else:
            print('form is invalid')
            print(form.errors)
    
    form = BlogPostForm()
    context = {
        'form': form
    }
    return render(request, 'dashboard/add_post.html', context)

@login_required
@user_passes_test(is_admin_user)
def edit_post(request, pk):
    post = get_object_or_404(Blog, pk=pk)
    was_published = getattr(post, 'status', 'Draft') == 'Published'
    
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            updated_post = form.save(commit=False)
            title = form.cleaned_data['title']
            
            # Generate new slug, but only if title changed
            new_slug = generate_unique_slug(title, updated_post.id)
            if updated_post.slug != new_slug:
                # Check if the new slug would conflict with existing posts (excluding current post)
                if not Blog.objects.filter(slug=new_slug).exclude(id=updated_post.id).exists():
                    updated_post.slug = new_slug
            
            updated_post.save()
            
            # CRITICAL: Save many-to-many relationships (TAGS!)
            form.save_m2m()
            
            # Check if post was just published (draft -> published)
            is_now_published = getattr(updated_post, 'status', 'Draft') == 'Published'
            
            if not was_published and is_now_published:
                try:
                    # Send newsletter only if post was just published for the first time
                    send_newsletter_email(updated_post)
                    messages.success(request, f'Post "{updated_post.title}" has been published and newsletter sent to subscribers!')
                    logger.info(f'Newsletter sent for newly published post: {updated_post.title}')
                except Exception as e:
                    messages.warning(request, f'Post published successfully, but failed to send newsletter: {str(e)}')
                    logger.error(f'Failed to send newsletter for post {updated_post.title}: {e}')
            else:
                messages.success(request, f'Post "{updated_post.title}" has been updated successfully.')
            
            return redirect('posts')
    
    form = BlogPostForm(instance=post)
    context = {
        'form': form,
        'post': post,
    }
    return render(request, 'dashboard/edit_post.html', context)

@login_required
@user_passes_test(is_admin_user)
@never_cache  # Never cache this view
def delete_post(request, pk):
    try:
        post = get_object_or_404(Blog, pk=pk)
        post_title = post.title
        post_id = post.id
        
        # Delete the post
        post.delete()
        
        # Clear cache after successful deletion
        cache.clear()  # Clear all cache
        # Or clear specific cache keys:
        # cache.delete_many([f'posts_list', f'post_{pk}', f'home_page'])
        
        messages.success(request, f'Post "{post_title}" has been deleted successfully.')
        logger.info(f'Post deleted: ID {post_id}, Title: "{post_title}" by user {request.user.username}')
        
    except Exception as e:
        messages.error(request, f'Error deleting post: {str(e)}')
        logger.error(f'Error deleting post {pk}: {e}')
    
    return redirect('posts')

def users(request):
    users = User.objects.all()
    context = {
        'users': users
    }
    return render(request, 'dashboard/users.html', context)

@login_required
@user_passes_test(is_admin_user)
@never_cache  # Never cache this view
def add_user(request):
    if request.method == 'POST':
        form = AddUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('users')
        else:
            print(form.errors)
    form = AddUserForm()
    context = {
        'form': form,
    }
    return render(request, 'dashboard/add_user.html', context)

@login_required
@user_passes_test(is_admin_user)
def edit_user(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = EditUserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('users')
    else:
        form = EditUserForm(instance=user)

    return render(request, 'dashboard/edit_user.html', {'form': form})

@login_required
@user_passes_test(is_admin_user)
@never_cache  # Never cache this view
def delete_user(request, pk):
    try:
        user = get_object_or_404(User, pk=pk)
        username = user.username
        user_id = user.id
        
        # Don't allow deleting superusers or the current user
        if user.is_superuser:
            messages.error(request, f'Cannot delete superuser "{username}".')
            return redirect('users')
        
        if user.id == request.user.id:
            messages.error(request, 'You cannot delete your own account.')
            return redirect('users')
        
        # Check if user has posts
        posts_count = Blog.objects.filter(author=user).count()
        if posts_count > 0:
            messages.warning(request, f'User "{username}" has {posts_count} posts. Consider reassigning them before deletion.')
        
        user.delete()
        
        # Clear cache after successful deletion
        cache.clear()  # Clear all cache
        
        messages.success(request, f'User "{username}" has been deleted successfully.')
        logger.info(f'User deleted: ID {user_id}, Username: "{username}" by user {request.user.username}')
        
    except Exception as e:
        messages.error(request, f'Error deleting user: {str(e)}')
        logger.error(f'Error deleting user {pk}: {e}')
    
    return redirect('users')