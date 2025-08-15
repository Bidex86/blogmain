from django.shortcuts import render, redirect, get_object_or_404
from blogs.models import Blog, Category
from django.contrib.auth.decorators import login_required,  user_passes_test
from . forms import BlogPostForm, CategoryForm, AddUserForm, EditUserForm
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from accounts.models import Profile
#from django.http import HttpResponse

# Create your views here.
def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@login_required(login_url='login')
@user_passes_test(is_admin_user)
def dashboard(request):
    category_count = Category.objects.all().count()
    blogs_count = Blog.objects.all().count()
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    context = {
        'category_count': category_count,
        'blogs_count': blogs_count,
        'profile': profile
    }
    return render(request, 'dashboard/dashboard.html', context)

def categories(request):
    #categories = Category.objects.all()

    return render(request, 'dashboard/categories.html') #{'categories': categories})

@login_required
@user_passes_test(is_admin_user)
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False) # temporarily saving the form
            category.save()
            category_name = form.cleaned_data['category_name']
            category.slug = slugify(category_name) + ''+str()
            category.save()
            form.save()
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
            category = form.save()
            category_name = form.cleaned_data['category_name']
            category.slug = slugify(category_name) + ''+str()
            category.save()
            form.save()
            return redirect('categories')
    form = CategoryForm(instance=category)
    context = {
        'form': form,
        'category': category
    }
    return render(request, 'dashboard/edit_category.html', context)

def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category.delete()
    return redirect('categories')

def posts(request):
    posts = Blog.objects.all()
    context = {
        'posts': posts,
    }
    return render(request, 'dashboard/posts.html', context)

@login_required
@user_passes_test(is_admin_user)
def add_post(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False) # temporarily saving the form
            post.author = request.user
        
            title = form.cleaned_data['title']
            post.slug = slugify(title) + ''+str()
            #post.save()
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
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save()
            title = form.cleaned_data['title']
            post.slug = slugify(title) + ''+str()
            post.save()
            return redirect('posts')
    form = BlogPostForm(instance=post)
    context = {
        'form': form,
        'post': post,
    }
    return render(request, 'dashboard/edit_post.html', context)

@login_required
@user_passes_test(is_admin_user)
def delete_post(request, pk):
    post = get_object_or_404(Blog, pk=pk)
    post.delete()
    return redirect('posts')

def users(request):
    users = User.objects.all()
    context = {
        'users': users
    }
    return render(request, 'dashboard/users.html', context)

@login_required
@user_passes_test(is_admin_user)
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
def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.delete()
    return redirect('users')