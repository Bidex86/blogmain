from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from taggit.models import Tag
from .models import Blog, Category
#from .forms import CommentForm
from django.db.models import Q
from django.db.models import Count
from django.http import JsonResponse
import json
from django.contrib.contenttypes.models import ContentType
from comments.models import Comment
from comments.forms import CommentForm
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.views.decorators.cache import never_cache, cache_control
from django.views.decorators.vary import vary_on_cookie


def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /dashboard/",
        "Allow: /",
        "",
        "Sitemap: https://yourdomain.com/sitemap.xml"  # Update with your domain
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def tag_suggestions(request):
    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse({'tags': []})

    tags = Tag.objects.filter(name__icontains=query).order_by('name')[:10]
    return JsonResponse({'tags': [tag.name for tag in tags]})


def tagged_posts(request, tag_slug):
    tag = get_object_or_404(Tag, slug=tag_slug)

    # Posts for this tag - OPTIMIZED with select_related
    posts = Blog.objects.select_related('category').filter(
        tags__in=[tag], 
        status='Published'
    ).order_by('-created_at')

    # Pagination for tagged posts
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # FIXED: Trending posts using views instead of comment count
    # Since you don't have a direct comment relationship, use views or created_at
    trending_posts = Blog.objects.select_related('category').filter(
        status='Published'
    ).order_by('-views', '-created_at')[:5]  # Order by views instead

    # Alternative: If you want to count comments properly, use this approach:
    """
    from django.contrib.contenttypes.models import ContentType
    blog_content_type = ContentType.objects.get_for_model(Blog)
    
    trending_posts = Blog.objects.select_related('category').filter(
        status='Published'
    ).annotate(
        comment_count=Count(
            'comment_set',
            filter=Q(comment_set__content_type=blog_content_type)
        )
    ).order_by('-comment_count', '-created_at')[:5]
    """

    # Editor's Picks: Recently published posts - OPTIMIZED
    editors_picks = Blog.objects.select_related('category').filter(
        is_editors_pick=True, 
        status='Published'
    ).order_by('-created_at')[:5]

    # Breadcrumbs
    breadcrumbs = [
        {'name': 'Home', 'url': '/'},
        {'name': f'Posts tagged "{tag.name}"', 'url': None}
    ]

    # SEO Meta
    meta_title = f"Posts tagged '{tag.name}' - Your Blog"
    meta_description = f"Browse all posts tagged with {tag.name}. Stay updated with the latest articles."

    return render(request, 'tagged_posts.html', {
        'tag': tag,
        'posts': page_obj,  # Use paginated posts
        'page_obj': page_obj,
        'trending_posts': trending_posts,
        'editors_picks': editors_picks,
        'breadcrumbs': breadcrumbs,
        'meta_title': meta_title,
        'meta_description': meta_description,
    })
@vary_on_cookie  # Cache differently for different users
@cache_control(private=True, max_age=0)  # Don't cache for authenticated users
def posts_by_category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    
    # OPTIMIZED: Use select_related to avoid N+1 queries
    all_posts = Blog.objects.select_related('category').filter(
        status='Published', 
        category=category
    ).order_by('-created_at')
    
    # OPTIMIZED: Editor's picks with select_related
    editors_picks = Blog.objects.select_related('category').filter(
        is_editors_pick=True, 
        status='Published'
    ).order_by('-created_at')[:5]
    
    # PAGINATION
    paginator = Paginator(all_posts, 10)  # Show 10 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Breadcrumbs
    breadcrumbs = [
        {'name': 'Home', 'url': '/'},
        {'name': category.category_name, 'url': None}
    ]
    
    context = {
        'category': category,
        'page_obj': page_obj,  # Contains paginated posts
        'posts': page_obj.object_list,  # For backward compatibility
        'all_posts': all_posts,  # Keep for any other template needs
        'editors_picks': editors_picks,
        'breadcrumbs': breadcrumbs,
        'meta_title': category.get_meta_title() if hasattr(category, 'get_meta_title') else f"{category.category_name} Articles",
        'meta_description': category.get_meta_description() if hasattr(category, 'get_meta_description') else f"Read the latest articles in {category.category_name}.",
    }
    return render(request, 'posts_by_category.html', context)

@cache_page(60 * 15)
def blogs(request, category_slug, slug):
    # OPTIMIZED: Get category and post with select_related
    category = get_object_or_404(Category, slug=category_slug)
    single_blog = get_object_or_404(
        Blog.objects.select_related('category', 'author').prefetch_related('tags'), 
        slug=slug, 
        status='Published',
        category=category  # Ensure post belongs to the category
    )
    post = single_blog  # For backward compatibility
    
    # OPTIMIZED: Recent posts with select_related
    posts = Blog.objects.select_related('category', 'author').filter(
        status='Published'
    ).exclude(id=single_blog.id).order_by('-created_at')[:5]

    # Increase view count
    single_blog.views += 1
    single_blog.save(update_fields=['views'])

    # OPTIMIZED: Related posts with select_related
    related_posts = Blog.objects.select_related('category', 'author').filter(
        category=single_blog.category,
        status='Published'
    ).exclude(
        id=single_blog.id
    ).order_by('-created_at')[:4]

    # OPTIMIZED: Comments with select_related for user
    # Get comments for this post
    content_type = ContentType.objects.get_for_model(Blog)

    # Get all categories for sidebar navigation
    categories = Category.objects.all().order_by('category_name')

    # Trending posts for sidebar
    trending_posts = Blog.objects.select_related('category').filter(
        status='Published'
    ).order_by('-views', '-created_at')[:5]

    # Breadcrumbs
    breadcrumbs = [
        {'name': 'Home', 'url': '/'},
        {'name': category.category_name, 'url': category.get_absolute_url()},
        {'name': single_blog.title, 'url': None}
    ]


    context = {
        'category': category,
        'posts': posts,
        'single_blog': single_blog,
        'post': post,  # Backward compatibility
        'related_posts': related_posts,
        'content_type_id': content_type.id,
        'comment_form': CommentForm(content_object=post),
        #'comments': comments_page,
        'breadcrumbs': breadcrumbs,
        'categories': categories,  # For sidebar navigation
        'trending_posts': trending_posts,  # For sidebar
        'structured_data': json.dumps(post.get_structured_data()) if hasattr(post, 'get_structured_data') else '{}',
        'reading_time': post.get_reading_time() if hasattr(post, 'get_reading_time') else 5,
        'word_count': post.get_word_count() if hasattr(post, 'get_word_count') else 0,
        'seo_score': post.get_seo_score() if hasattr(post, 'get_seo_score') else 0,
    }
    return render(request, 'blogs.html', context)

def search(request):
    keyword = request.GET.get('keyword')
    
    if keyword:
        # FIXED: Use correct field names from your Blog model
        blogs = Blog.objects.select_related('category').filter(
            Q(title__icontains=keyword) | 
            Q(short_description__icontains=keyword) | 
            Q(blog_body__icontains=keyword) |
            Q(seo_keywords__icontains=keyword) |  # CHANGED: meta_keywords -> seo_keywords
            Q(focus_keyword__icontains=keyword),
            status='Published'
        ).order_by('-created_at')
        
        # Pagination for search results
        paginator = Paginator(blogs, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    else:
        blogs = Blog.objects.none()
        page_obj = None
    
    # Breadcrumbs
    breadcrumbs = [
        {'name': 'Home', 'url': '/'},
        {'name': f'Search results for "{keyword}"' if keyword else 'Search', 'url': None}
    ]
    
    # SEO Meta
    meta_title = f'Search results for "{keyword}"' if keyword else 'Search'
    meta_description = f'Search results for "{keyword}" on our blog.' if keyword else 'Search our blog for articles, news, and updates.'
    
    context = {
        'blogs': blogs,
        'page_obj': page_obj,
        'keyword': keyword,
        'breadcrumbs': breadcrumbs,
        'meta_title': meta_title,
        'meta_description': meta_description,
        'result_count': blogs.count() if keyword else 0,
    }
    return render(request, 'search.html', context)