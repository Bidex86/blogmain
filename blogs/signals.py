from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.conf import settings
from accounts.models import Profile
from .models import Blog
from django.core.files.storage import default_storage
import os, re
from io import BytesIO
from PIL import Image, ImageOps
from django.core.files.base import ContentFile
from pathlib import Path


# ---------------- EMAIL ALERT ---------------- #
@receiver(post_save, sender=Blog)
def send_new_post_email(sender, instance, created, **kwargs):
    # Only send email for published posts, not drafts
    if created and getattr(instance, 'status', 'Draft') == 'Published':
        try:
            subject = f"New post: {instance.title}"
            from_email = 'bidemia02@gmail.com'
            recipient_list = [u.email for u in User.objects.filter(profile__newsletter_opt_in=True)]
            
            # Use the same template as your manual email system
            html_content = render_to_string('emails/add_post.html', {
                'post': instance,
                'request': None  # You might need to pass request context if needed
            })
            
            # Create better text content
            if hasattr(instance, 'short_description') and instance.short_description:
                text_content = instance.short_description
            else:
                text_content = getattr(instance, 'blog_body', instance.body or '')[:200] + '...'

            msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            print(f"Newsletter sent via signal for published post: {instance.title}")
            
        except Exception as e:
            print(f"Error sending newsletter via signal: {e}")


WEBP_QUALITY = 80
JPEG_QUALITY = 80
SIZES = [150, 320, 480, 768, 1024]  # includes sidebar sizes

# ----------------
# Helpers
# ----------------
def slugify_filename(title):
    """Convert blog title into SEO-friendly filename."""
    return re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

def resize_and_save(img, base_name, ext, width, quality, fmt):
    """Resize image to given width and return ContentFile."""
    img_copy = img.copy()
    img_copy.thumbnail(
        (width, width * img_copy.height // img_copy.width),
        Image.LANCZOS
    )
    img_io = BytesIO()
    save_kwargs = {"optimize": True}
    if fmt != "PNG":
        save_kwargs["quality"] = quality
    img_copy.save(img_io, format=fmt, **save_kwargs)
    return ContentFile(img_io.getvalue(), name=f"{base_name}-{width}{ext}")

def delete_old_files(instance):
    """Delete old original, WebP, and resized files."""
    if not instance.featured_image:
        return
    try:
        orig_path = instance.featured_image.path
        base, _ = os.path.splitext(orig_path)
        dir_name = os.path.dirname(orig_path)
        resized_dir = os.path.join(dir_name, "resized")

        if os.path.isfile(orig_path):
            os.remove(orig_path)
        if os.path.isfile(f"{base}.webp"):
            os.remove(f"{base}.webp")
        if os.path.isdir(resized_dir):
            for f in os.listdir(resized_dir):
                if f.startswith(os.path.basename(base)):
                    os.remove(os.path.join(resized_dir, f))
    except Exception as e:
        print(f"[Cleanup error] {e}")

# ----------------
# Cleanup
# ----------------
@receiver(pre_delete, sender=Blog)
def cleanup_images_on_delete(sender, instance, **kwargs):
    delete_old_files(instance)

# ----------------
# Optimization
# ----------------
@receiver(post_save, sender=Blog)
def optimize_images(sender, instance, **kwargs):
    if not instance.featured_image:
        return

    try:
        image_path = instance.featured_image.path
    except Exception:
        return

    ext = os.path.splitext(image_path)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png']:
        return

    img = ImageOps.exif_transpose(Image.open(image_path))
    img = img.convert("RGB")

    # Save image dimensions
    instance.image_width, instance.image_height = img.size

    # SEO-friendly base name
    base_name = slugify_filename(instance.title)
    instance.image_base_name = base_name

    original_dir = os.path.dirname(image_path)
    resized_dir = os.path.join(original_dir, "resized")
    os.makedirs(resized_dir, exist_ok=True)

    optimized_path = os.path.join(original_dir, f"{base_name}{ext}")

    # --- 1) Compress & save optimized original ---
    img_io = BytesIO()
    if ext == ".png":
        img.save(img_io, format="PNG", optimize=True)
    else:
        img.save(img_io, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    with open(optimized_path, "wb") as f:
        f.write(img_io.getvalue())

    # --- 2) Main WebP ---
    try:
        webp_path = os.path.join(original_dir, f"{base_name}.webp")
        webp_io = BytesIO()
        img.save(webp_io, format="WEBP", quality=WEBP_QUALITY, optimize=True)
        with open(webp_path, "wb") as f:
            f.write(webp_io.getvalue())
    except Exception as e:
        print(f"[WebP generation error] {e}")

    # --- 3) Resized versions ---
    for size in SIZES:
        try:
            resized_file = resize_and_save(
                img, base_name, ext, size, JPEG_QUALITY,
                "JPEG" if ext != ".png" else "PNG"
            )
            with open(os.path.join(resized_dir, resized_file.name), "wb") as f:
                f.write(resized_file.read())
        except Exception as e:
            print(f"[Resize error JPG/PNG] {e}")

        try:
            resized_webp = resize_and_save(img, base_name, ".webp", size, WEBP_QUALITY, "WEBP")
            with open(os.path.join(resized_dir, resized_webp.name), "wb") as f:
                f.write(resized_webp.read())
        except Exception as e:
            print(f"[Resize error WebP] {e}")

    # --- 4) Update featured_image path to optimized file ---
    if default_storage.exists(optimized_path):
        instance.featured_image.name = os.path.relpath(optimized_path, settings.MEDIA_ROOT)

    # --- 5) Save updated fields without triggering loop ---
    Blog.objects.filter(pk=instance.pk).update(
        featured_image=instance.featured_image.name,
        image_base_name=base_name,
        image_width=instance.image_width,
        image_height=instance.image_height
    )

    # --- 6) Delete original uploaded file if different ---
    if image_path != optimized_path and os.path.exists(image_path):
        try:
            os.remove(image_path)
        except Exception as e:
            print(f"[Cleanup original error] {e}")