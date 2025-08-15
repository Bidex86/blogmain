from django.shortcuts import render
from django.core.paginator import Paginator
from blogs.models import Blog, Category


def home(request):
    # Featured post
    featured_post = Blog.objects.filter(is_featured=True, status='Published').order_by('-created_at').first()


    # Trending posts (e.g. most viewed or most recent)
    trending_posts = Blog.objects.order_by('-views')[:2]

    # Editor's picks (e.g. manually selected)
    editors_picks = Blog.objects.filter(is_editors_pick=True, status='Published').order_by('-created_at')[:5]
    #categories = Category.objects.all()

    # Recent posts with pagination
    posts = Blog.objects.filter(status='Published').order_by('-created_at')
    paginator = Paginator(posts, 10)  # Show 6 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Posts grouped by category
    categories = Category.objects.all()
    category_posts = {
        category: Blog.objects.filter(category=category, status='Published').order_by('-created_at')[:6]
        for category in categories
    }



    context = {
        'featured_post': featured_post,
        'trending_posts': trending_posts,
        'editors_picks': editors_picks,
        'page_obj': page_obj,
        'category_posts': category_posts,
        }
    return render(request, 'home.html', context)

    
