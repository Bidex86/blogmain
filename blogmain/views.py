
from django.shortcuts import render, redirect
from blogs.models import Blog, Category
#from assignment.models import About
from django.core.paginator import Paginator
from .forms import RegistrationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import auth 

def home(request):
    featured_posts = Blog.objects.filter(is_featured=True, status='Published').order_by('updated_at')
    all_posts = Blog.objects.filter(is_featured=False, status='Published')

    # PAGINATION
    paginator = Paginator(all_posts, 5)  # Show 5 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
            'featured_posts': featured_posts,
            'posts': all_posts,
            'page_obj': page_obj,
            #'about': about,
        }
    return render(request, 'home.html', context)

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        else:
            print(form.errors)
    else:
        form = RegistrationForm()
    context = {
        'form': form,
    }
    return render(request, 'register.html', context)

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = auth.authenticate(username=username, password=password)
            if user is not None:
                auth.login(request, user)
                # Redirect based on role
                if user.is_staff or user.is_superuser:
                    return redirect('dashboard')
                else:
                    return redirect('home')
            

    form = AuthenticationForm()
    context = {
        'form': form,
    }
    return render(request, 'login.html', context)

def logout(request):
    auth.logout(request)
    return redirect('home')