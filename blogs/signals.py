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
from moviepy import VideoFileClip
from django.core.files.base import ContentFile
from pathlib import Path
from django.db.models.signals import post_save
from comments.models import Comment
from notifications.views import create_notification, send_push_notification, NotificationPreference, notify_users_new_post

# ---------------- EMAIL ALERT ---------------- #
@receiver(post_save, sender=Blog)
def send_new_post_email(sender, instance, created, **kwargs):
    """Send email and push notifications for published posts"""
    if created and getattr(instance, 'status', 'Draft') == 'Published':
        try:
            # Send email (existing code)
            subject = f"New post: {instance.title}"
            from_email = 'bidemia02@gmail.com'
            recipient_list = [u.email for u in User.objects.filter(profile__newsletter_opt_in=True)]
            
            html_content = render_to_string('emails/add_post.html', {
                'post': instance,
                'request': None
            })
            
            if hasattr(instance, 'short_description') and instance.short_description:
                text_content = instance.short_description
            else:
                text_content = getattr(instance, 'blog_body', instance.body or '')[:200] + '...'

            msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            print(f"Newsletter sent via email for: {instance.title}")
            
            # Send push notifications using the new system
            notify_users_new_post(instance)
            
        except Exception as e:
            print(f"Error sending notifications: {e}")

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
# Cleanup - UPDATED to handle video files
# ----------------
@receiver(pre_delete, sender=Blog)
def cleanup_media_on_delete(sender, instance, **kwargs):
    """Delete images and videos when blog post is deleted"""
    # Clean up images
    delete_old_files(instance)
    
    # ADDED: Clean up video files
    try:
        if instance.video_file:
            if os.path.isfile(instance.video_file.path):
                os.remove(instance.video_file.path)
                print(f"[Video cleanup] Deleted video: {instance.video_file.path}")
        
        if instance.video_thumbnail:
            if os.path.isfile(instance.video_thumbnail.path):
                os.remove(instance.video_thumbnail.path)
                print(f"[Video cleanup] Deleted thumbnail: {instance.video_thumbnail.path}")
    except Exception as e:
        print(f"[Video cleanup error] {e}")

# ----------------
# Image Optimization
# ----------------
@receiver(post_save, sender=Blog)
def optimize_images(sender, instance, created, **kwargs):
    """Optimize and resize featured images"""
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

# ----------------
# Video Processing - FIXED VERSION
# ----------------
@receiver(post_save, sender=Blog)
def process_video_metadata(sender, instance, created, update_fields, **kwargs):
    """
    Extract video metadata like duration and generate thumbnail
    Only runs if video_file exists and duration is not set
    
    FIXED ISSUES:
    1. Added update_fields parameter to prevent infinite loop
    2. Added check to skip if already processing
    3. Import errors handled gracefully
    """
    # CRITICAL FIX 1: Skip if this save was triggered by our update
    if update_fields is not None and 'video_duration' in update_fields:
        return
    
    # Skip if no video or already processed
    if not instance.video_file or instance.video_duration:
        return
    
    # CRITICAL FIX 2: Check if moviepy is installed
    try:
        from moviepy import VideoFileClip
    except ImportError:
        print("[Video processing] moviepy not installed. Run: pip install moviepy")
        return
    
    try:
        from datetime import timedelta
        
        # Get video file path
        video_path = instance.video_file.path
        
        # Check if file exists
        if not os.path.isfile(video_path):
            print(f"[Video processing] Video file not found: {video_path}")
            return
        
        print(f"[Video processing] Processing video for: {instance.title}")
        
        # Open video
        clip = VideoFileClip(video_path)
        
        # Extract duration
        duration = timedelta(seconds=int(clip.duration))
        print(f"[Video processing] Duration: {duration}")
        
        # Generate thumbnail at 1 second (if not already set)
        thumbnail_generated = False
        if not instance.video_thumbnail:
            try:
                # Get frame at 1 second (or 0 if video is shorter)
                frame_time = min(1, clip.duration - 0.1)
                frame = clip.get_frame(frame_time)
                img = Image.fromarray(frame)
                
                # Optimize thumbnail
                img.thumbnail((1280, 720), Image.LANCZOS)
                
                # Save thumbnail
                thumb_io = BytesIO()
                img.save(thumb_io, format='JPEG', quality=85, optimize=True)
                thumb_io.seek(0)
                
                thumb_name = f"{instance.slug}-video-thumb.jpg"
                instance.video_thumbnail.save(
                    thumb_name,
                    ContentFile(thumb_io.read()),
                    save=False
                )
                thumbnail_generated = True
                print(f"[Video processing] Thumbnail generated: {thumb_name}")
            except Exception as thumb_error:
                print(f"[Video processing] Thumbnail generation failed: {thumb_error}")
        
        # Close the video clip
        clip.close()
        
        # CRITICAL FIX 3: Use update_fields to prevent triggering signal again
        update_data = {'video_duration': duration}
        if thumbnail_generated and instance.video_thumbnail:
            update_data['video_thumbnail'] = instance.video_thumbnail.name
        
        Blog.objects.filter(pk=instance.pk).update(**update_data)
        
        print(f"[Video processing] Successfully processed video for: {instance.title}")
        
    except Exception as e:
        print(f"[Video processing error] {e}")
        import traceback
        traceback.print_exc()
        # Don't fail the save if video processing fails

# ----------------
# Comment Notifications
# ----------------
@receiver(post_save, sender=Comment)
def send_comment_notifications(sender, instance, created, **kwargs):
    """Send notifications when new comments or replies are posted"""
    if not created:
        return
    
    from django.contrib.contenttypes.models import ContentType
    from blogs.models import Blog
    from django.utils.html import strip_tags
    
    # Get the blog post
    blog_content_type = ContentType.objects.get_for_model(Blog)
    
    if instance.content_type == blog_content_type:
        blog_post = instance.content_object
        
        # Clean comment content
        clean_content = strip_tags(instance.content)[:100]
        
        # If this is a reply to another comment
        if instance.parent:
            parent_author = instance.parent.user
            
            if parent_author != instance.user:
                try:
                    preference = NotificationPreference.objects.get(user=parent_author)
                    if not preference.notify_comment_replies:
                        return
                except NotificationPreference.DoesNotExist:
                    pass
                
                notification = create_notification(
                    user=parent_author,
                    notif_type='comment_reply',
                    title=f"{instance.user.username} replied to your comment",
                    message=clean_content,
                    url=blog_post.get_absolute_url() if hasattr(blog_post, 'get_absolute_url') else '/',
                    blog_post=blog_post,
                    comment=instance,
                )
                
                send_push_notification(
                    user=parent_author,
                    title=notification.title,
                    body=clean_content,
                    url=notification.url,
                )
                
                notification.is_sent = True
                notification.save()
        
        else:
            # This is a new top-level comment
            post_author = blog_post.author
            
            if post_author != instance.user:
                try:
                    preference = NotificationPreference.objects.get(user=post_author)
                    if not preference.notify_comments:
                        return
                except NotificationPreference.DoesNotExist:
                    pass
                
                notification = create_notification(
                    user=post_author,
                    notif_type='new_comment',
                    title=f"{instance.user.username} commented on your post",
                    message=f'"{blog_post.title}": {clean_content}',
                    url=blog_post.get_absolute_url() if hasattr(blog_post, 'get_absolute_url') else '/',
                    blog_post=blog_post,
                    comment=instance,
                )
                
                send_push_notification(
                    user=post_author,
                    title=notification.title,
                    body=notification.message,
                    url=notification.url,
                )
                
                notification.is_sent = True
                notification.save()
