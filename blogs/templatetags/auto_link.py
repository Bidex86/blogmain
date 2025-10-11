import re
from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.html import escape

register = template.Library()

# Regex to split content but keep <a> tags and also headings/bold tags
ANCHOR_HEADING_BOLD_SPLIT_RE = re.compile(
    r'(<a\b[^>]*>.*?</a>|<h[1-6]\b[^>]*>.*?</h[1-6]>|<strong\b[^>]*>.*?</strong>|<b\b[^>]*>.*?</b>)',
    re.IGNORECASE | re.DOTALL
)

def _link_once(text: str, keyword: str, url: str) -> str:
    """Link the first occurrence of keyword in text."""
    if not keyword:
        return text
    pattern = re.compile(r'\b(' + re.escape(keyword) + r')\b', re.IGNORECASE)
    return pattern.sub(rf'<a href="{url}">\1</a>', text, count=1)

@register.simple_tag
def auto_link_bundle(content, related_posts):
    """
    Auto-links keywords in content from related_posts.
    Returns: {
        'content': processed content with auto-links,
        'linked_ids': list of linked post IDs,
        'related_links': list of dicts with post info for template use
    }
    """
    if not content:
        return {'content': '', 'linked_ids': [], 'related_links': []}

    segments = ANCHOR_HEADING_BOLD_SPLIT_RE.split(str(content))
    linked_ids = []
    related_links = []

    def link_in_segments(keywords, url):
        """Insert one link in non-anchor, non-heading, non-bold segments."""
        for i, seg in enumerate(segments):
            if i % 2 == 1:  # These are skipped tags
                continue
            before = seg
            for kw in keywords:
                new = _link_once(before, kw, url)
                if new != before:
                    segments[i] = new
                    return True
        return False

    # Auto-link from related posts and build related_links list
    for p in related_posts:
        if not getattr(p, 'slug', None) or not getattr(p, 'category', None):
            continue
        try:
            url = reverse('blogs', kwargs={'category_slug': p.category.slug, 'slug': p.slug})
        except Exception as e:
            print(f"Error generating URL for {p.title}: {e}")
            continue

        # Try to link keywords in content
        keywords = [k.strip() for k in str(p.seo_keywords).split(',')] if getattr(p, 'seo_keywords', None) else [p.title.strip()]
        if link_in_segments(keywords, url):
            linked_ids.append(p.id)

        # Build related_links for template use
        related_links.append({
            'title': p.title,
            'url': url,
            'excerpt': getattr(p, 'short_description', ''),
            'post': p
        })

    # DON'T insert inline content - let the template handle it
    # This prevents the layout breaking issue
    processed_content = ''.join(segments)

    return {
        'content': mark_safe(processed_content), 
        'linked_ids': linked_ids,
        'related_links': related_links[:6]
    }

@register.filter
def exclude_ids(posts, ids):
    """Exclude posts whose IDs are in the given list."""
    if not posts or not ids:
        return posts
    return [post for post in posts if post.id not in ids]