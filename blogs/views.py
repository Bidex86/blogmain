from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect

from .models import Blog, Category, Comment
from .forms import CommentForm
from django.db.models import Q

# Create your views here.
def posts_by_category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    all_posts = Blog.objects.filter(status='Published', category=category)

    # PAGINATION
    paginator = Paginator(all_posts, 5)  # Show 5 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': all_posts,
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'posts_by_category.html', context)


def blogs(request, category_slug, slug):
    category = get_object_or_404(Category, slug=category_slug)
    single_blog = get_object_or_404(Blog, slug=slug, status='Published')
    posts = Blog.objects.filter(is_featured=False, status='Published')

     # Top-level comments only
    comments = Comment.objects.filter(blog=single_blog, parent__isnull=True).order_by('-created_at')
    comment_count = Comment.objects.filter(blog=single_blog).count()

    form = CommentForm()

    if request.method == 'POST':
        form = CommentForm(request.POST)
        parent_id = request.POST.get('parent_id')  # comes from hidden input

        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.blog = single_blog
            if parent_id:
                try:
                    comment.parent = Comment.objects.get(id=parent_id)
                except Comment.DoesNotExist:
                    comment.parent = None
            comment.save()
            return HttpResponseRedirect(request.path_info)  # refresh page cleanly

    
    context = {
        'category': category,
        'posts': posts,
        'single_blog': single_blog,
        'comments': comments,
        'comment_count': comment_count,
        'form': form,
    }
    return render(request, 'blogs.html', context)

def search(request):
    keyword = request.GET.get('keyword')
    
    blogs = Blog.objects.filter(Q(title__icontains=keyword) | Q(short_description__icontains=keyword) | Q(blog_body__icontains=keyword), status='Published')
    
    context = {
        'blogs': blogs,
        'keyword': keyword,
    }
    return render(request, 'search.html', context)

