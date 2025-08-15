from django import template
from django.utils.html import format_html, escape
from urllib.parse import urljoin
import os
from blogs.models import Blog
from blogs.signals import SIZES

register = template.Library()

# Track first image render in this request
_rendered_first_image = {}

IMAGE_CONTEXTS = {
    "default": SIZES,
    "sidebar": [150, 300],
    "post": [150, 320, 480, 768],  # Added small size for mobile
    "full": [768, 1024],
}

SIZES_ATTRS = {
    "default": "100vw",
    "sidebar": "(max-width: 600px) 50vw, 150px",
    "post": "100vw",
    "full": "100vw"
}

PLACEHOLDER_IMG = "/static/images/placeholder.jpg"


@register.simple_tag(takes_context=True)
def seo_responsive_image(context, source, alt="", css_class="", context_name="default", widths=None, loading="lazy"):
    """
    Outputs a responsive <picture> element with WebP + fallback.
    First image in the post gets loading="eager" for better LCP.
    Uses a resized version for the <img src> to improve LCP.
    """
    request_id = id(context)  # Unique per-render
    if request_id not in _rendered_first_image:
        loading = "eager"  # First image is eager-loaded
        _rendered_first_image[request_id] = True

    if widths is None:
        widths = IMAGE_CONTEXTS.get(context_name, SIZES)

    sizes_attr = SIZES_ATTRS.get(context_name, "100vw")
    fallback_width = max(w for w in widths if w <= 768) if any(w <= 768 for w in widths) else min(widths)

    # Case 1: Source is a Blog object
    if isinstance(source, Blog):
        if not source.featured_image:
            return _placeholder_img(alt, css_class, loading)

        base_name = source.image_base_name or os.path.splitext(os.path.basename(source.featured_image.name))[0]
        try:
            orig_url = source.featured_image.url
        except ValueError:
            return _placeholder_img(alt, css_class, loading)

        orig_dir = os.path.dirname(orig_url)
        resized_dir = urljoin(orig_dir + "/", "resized/")
        ext = os.path.splitext(orig_url)[1].lower()

        width_attr = f' width="{source.image_width}"' if source.image_width else ""
        height_attr = f' height="{source.image_height}"' if source.image_height else ""

    # Case 2: Source is a direct string path/URL
    elif isinstance(source, str):
        base_name = os.path.splitext(os.path.basename(source))[0]
        ext = os.path.splitext(source)[1].lower()
        orig_url = source
        resized_dir = urljoin(os.path.dirname(source) + "/", "resized/")
        width_attr = height_attr = ""
    else:
        return _placeholder_img(alt, css_class, loading)

    alt_escaped = escape(alt)
    css_class_attr = css_class or ""
    size_attrs = f"{width_attr}{height_attr}"

    srcset_webp = ", ".join(
        f"{resized_dir}{base_name}-{w}.webp {w}w" for w in widths
    )
    srcset_orig = ", ".join(
        f"{resized_dir}{base_name}-{w}{ext} {w}w" for w in widths
    )

    # Use a medium-sized fallback for immediate LCP boost
    fallback_src_webp = f"{resized_dir}{base_name}-{fallback_width}.webp"
    fallback_src_orig = f"{resized_dir}{base_name}-{fallback_width}{ext}"

    # Check if webp fallback exists, otherwise use jpg/png fallback
    fallback_src = fallback_src_webp if ext != ".png" else fallback_src_orig

    html = format_html(
        '<picture>'
        '<source type="image/webp" srcset="{}" sizes="{}">'
        '<source type="image/{}" srcset="{}" sizes="{}">'
        '<img src="{}" alt="{}" loading="{}" class="{}"{}>'
        '</picture>',
        srcset_webp, sizes_attr,
        ext.strip('.'), srcset_orig, sizes_attr,
        fallback_src, alt_escaped, loading, css_class_attr, size_attrs
    )

    return html


def _placeholder_img(alt, css_class, loading):
    return format_html(
        '<img src="{}" alt="{}" class="{}" loading="{}">',
        PLACEHOLDER_IMG, escape(alt), css_class, loading
    )
