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
from ads.models import Advertisement, AdPosition
from blogs.ai_content import AIContentIntelligence
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from blogs.link_building import AILinkBuilder



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

    # Add advertisement analytics (only for staff)
    ad_analytics = None
    if request.user.is_staff:
        ad_analytics = get_simple_ad_analytics()
    
    context = {
        'category_count': category_count,
        'blogs_count': blogs_count,
        'profile': profile,
        'users_count': users_count,
        'ad_analytics': ad_analytics,
        'show_ad_analytics': request.user.is_staff,
    }
    return render(request, 'dashboard/dashboard.html', context)

def get_simple_ad_analytics():
    """Simple analytics - just the essentials"""
    from ads.models import Advertisement
    
    # Calculate basic stats
    total_impressions = sum(ad.impressions for ad in Advertisement.objects.filter(is_active=True))
    total_clicks = sum(ad.clicks for ad in Advertisement.objects.filter(is_active=True))
    active_ads_count = Advertisement.objects.filter(is_active=True).count()
    overall_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    
    return {
        'total_impressions': total_impressions,
        'total_clicks': total_clicks,
        'overall_ctr': overall_ctr,
        'active_ads_count': active_ads_count,
    }

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

@never_cache  # Never cache this view
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
@never_cache
def add_post(request):
    # Initialize variables
    post = None
    ai_analysis = None
    
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
            
            # Run AI analysis after saving
            try:
                ai_analyzer = AIContentIntelligence(post)
                ai_analysis = ai_analyzer.analyze_content()
                # Store analysis in session
                #request.session['ai_analysis'] = ai_analysis

                # OPTIONAL: Run link building analysis
                link_builder = AILinkBuilder()
                link_suggestions = link_builder.generate_link_suggestions(post)
                ai_analysis['link_suggestions'] = link_suggestions

            except Exception as e:
                print(f"AI Analysis failed: {e}")
                ai_analysis = None
            
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
    else:
        # GET request - create new form
        form = BlogPostForm()
    
    context = {
        'form': form,
        'post': post,  # Will be None for GET requests
        'ai_analysis': ai_analysis,  # Will be None for GET requests
    }
    return render(request, 'dashboard/add_post.html', context)

@login_required
@user_passes_test(is_admin_user)
def edit_post(request, pk):
    post = get_object_or_404(Blog, pk=pk)
    was_published = getattr(post, 'status', 'Draft') == 'Published'

    # Run AI analysis on existing content
    ai_analyzer = AIContentIntelligence(post)
    ai_analysis = ai_analyzer.analyze_content()

    # OPTIONAL: Run link building analysis
    link_builder = AILinkBuilder()
    link_suggestions = link_builder.generate_link_suggestions(post)
    ai_analysis['link_suggestions'] = link_suggestions
    
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
        
    # Re-run analysis after changes
        ai_analyzer = AIContentIntelligence(post)
        ai_analysis = ai_analyzer.analyze_content()

        # OPTIONAL: Run link building analysis
        link_builder = AILinkBuilder()
        link_suggestions = link_builder.generate_link_suggestions(post)
        ai_analysis['link_suggestions'] = link_suggestions
    
    form = BlogPostForm(instance=post)
    context = {
        'form': form,
        'post': post,
        'ai_analysis': ai_analysis
    }
    return render(request, 'dashboard/edit_post.html', context)

# NEW: Add this AJAX endpoint for real-time analysis
@csrf_exempt
def analyze_content_ajax(request):
    """AJAX endpoint for real-time content analysis"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Create temporary post object for analysis
            class TempPost:
                def __init__(self, title, content, focus_keyword=''):
                    self.title = title
                    self.blog_body = content
                    self.focus_keyword = focus_keyword
                    
                def get_meta_description(self):
                    return data.get('meta_description', '')
            
            temp_post = TempPost(
                title=data.get('title', ''),
                content=data.get('content', ''),
                focus_keyword=data.get('focus_keyword', '')
            )
            
            ai_analyzer = AIContentIntelligence(temp_post)
            analysis = ai_analyzer.analyze_content()
            
            return JsonResponse({
                'success': True,
                'analysis': analysis
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

# NEW: Add this for analyzing existing posts
def analyze_existing_post(request, post_id):
    """Analyze an existing post and return results"""
    post = get_object_or_404(Blog, id=post_id)
    
    ai_analyzer = AIContentIntelligence(post)
    analysis = ai_analyzer.analyze_content()
    
    return JsonResponse({ 
        'success': True,
        'analysis': analysis,
        'post_id': post_id
    })

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