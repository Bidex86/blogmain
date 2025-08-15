from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from taggit.models import Tag
from .models import Blog, Category, Comment
from .forms import CommentForm
from django.db.models import Q
from django.db.models import Count
from django.http import JsonResponse
from django.http import HttpResponse


def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Disallow:",
        "Sitemap: https://127.0.0.1:8000/sitemap.xml"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


# Create your views here.
def tag_suggestions(request):
    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse({'tags': []})

    tags = Tag.objects.filter(name__icontains=query).order_by('name')[:10]
    return JsonResponse({'tags': [tag.name for tag in tags]})


def tagged_posts(request, tag_slug):
    tag = get_object_or_404(Tag, slug=tag_slug)

    # Posts for this tag
    posts = Blog.objects.filter(tags__in=[tag]).order_by('-created_at')

    # Trending posts: Most commented posts
    trending_posts = Blog.objects.annotate(
        comment_count=Count('comment')
    ).order_by('-comment_count', '-created_at')[:5]

    # Editor's Picks: Recently published posts (you can also filter by a boolean field if you have one)
    editors_picks = Blog.objects.order_by('-created_at')[:5]

    return render(request, 'tagged_posts.html', {
        'tag': tag,
        'posts': posts,
        'trending_posts': trending_posts,
        'editors_picks': editors_picks,
    })
def posts_by_category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    all_posts = Blog.objects.filter(status='Published', category=category)
    editors_picks = Blog.objects.filter(is_editors_pick=True, status='Published').order_by('-created_at')[:5]
    

    # PAGINATION
    paginator = Paginator(all_posts, 5)  # Show 5 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    
    context = {
        'all_posts': all_posts,
        'category': category,
        'page_obj': page_obj,
        'editors_picks': editors_picks
    }
    return render(request, 'posts_by_category.html', context)


def blogs(request, category_slug, slug):
    category = get_object_or_404(Category, slug=category_slug)
    single_blog = get_object_or_404(Blog, slug=slug, status='Published')
    post = get_object_or_404(Blog, slug=slug, category__slug=category_slug)
    posts = Blog.objects.filter(is_featured=False, is_editors_pick=False, status='Published')

    # Increase view count
    post.views += 1
    post.save(update_fields=['views'])

    # In your blogs view
    related_posts = Blog.objects.filter(
        category=post.category,
        status='Published'
    ).exclude(
        id=post.id
    ).exclude(
        slug__isnull=True
    ).exclude(
        slug=''
    )[:5]

    # Top-level comments
    comments = Comment.objects.filter(blog=single_blog, parent__isnull=True).order_by('-created_at')
    comment_count = Comment.objects.filter(blog=single_blog).count()

    form = CommentForm()

    if request.method == 'POST':
        form = CommentForm(request.POST)
        parent_id = request.POST.get('parent_id')

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
            return HttpResponseRedirect(request.path_info)

    context = {
        'category': category,
        'posts': posts,
        'single_blog': single_blog,
        'post': post,
        'related_posts': related_posts,  # ✅ Pass to template
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

