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
    Auto-links keywords in content from related_posts,
    and inserts related articles inline + at the bottom.
    """
    if not content:
        return {'content': '', 'linked_ids': []}

    segments = ANCHOR_HEADING_BOLD_SPLIT_RE.split(str(content))
    linked_ids = []

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

    # Auto-link from related posts
    for p in related_posts:
        if not getattr(p, 'slug', None) or not getattr(p, 'category', None):
            continue
        try:
            url = reverse('blogs', kwargs={'category_slug': p.category.slug, 'slug': p.slug})
        except Exception:
            continue

        keywords = [k.strip() for k in str(p.seo_keywords).split(',')] if getattr(p, 'seo_keywords', None) else [p.title.strip()]
        if link_in_segments(keywords, url):
            linked_ids.append(p.id)

    # Insert related articles inside content
    if related_posts:
        inline_posts = related_posts[:4]
        more_posts = related_posts[4:]

        inline_html = '<div class="related-inline"><h4>Read also</h4><ul>'
        for rp in inline_posts:
            try:
                url = reverse('blogs', kwargs={'category_slug': rp.category.slug, 'slug': rp.slug})
            except Exception:
                continue
            inline_html += f'<li><a href="{escape(url)}">{escape(rp.title)}</a></li>'
        inline_html += '</ul></div>'

        # Place after 2nd paragraph
        paragraphs = re.split(r'(</p>)', ''.join(segments), flags=re.IGNORECASE)
        insert_pos = min(4, len(paragraphs))
        paragraphs.insert(insert_pos, inline_html)
        segments = [''.join(paragraphs)]

        # Add bottom section for the rest
        if more_posts:
            bottom_html = '<div class="related-more"><h3>More</h3><ul>'
            for rp in more_posts:
                try:
                    url = reverse('blogs', kwargs={'category_slug': rp.category.slug, 'slug': rp.slug})
                except Exception:
                    continue
                bottom_html += f'<li><a href="{url}">{rp.title}</a></li>'
            bottom_html += '</ul></div>'
            segments.append(bottom_html)

    processed = ''.join(segments)
    return {'content': mark_safe(processed), 'linked_ids': linked_ids}

@register.filter
def exclude_ids(posts, ids):
    """Exclude posts whose IDs are in the given list."""
    if not posts or not ids:
        return posts
    return [post for post in posts if post.id not in ids]
