from .models import Category, SiteSetting, SocialLink
#from assignment.models import SocialLink


def get_categories(request):
    categories = Category.objects.all()
    return dict(categories=categories)


def get_social_links(request):
    return {
        'social_links': SocialLink.objects.all()
    }

def site_settings(request):
    settings = SiteSetting.objects.first()
    return {'site_settings': settings}