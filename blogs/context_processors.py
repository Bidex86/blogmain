from .models import Category, SiteSetting, SocialLink
#from assignment.models import SocialLink


def get_categories(request):
    categories = Category.objects.all()
    nav_categories = (
        Category.objects
        .filter(parent__isnull=True)
        .prefetch_related('children')
        .order_by('category_name')
    )
    return dict(categories=categories, nav_categories=nav_categories)


def get_social_links(request):
    return {
        'social_links': SocialLink.objects.all()
    }

def site_settings(request):
    settings = SiteSetting.objects.first()
    return {'site_settings': settings}