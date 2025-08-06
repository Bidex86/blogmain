from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.contrib.auth.models import User
from accounts.models import Profile
from .models import Blog  # or Blog if that's your model name
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


@receiver(post_save, sender=Blog)
def send_new_post_email(sender, instance, created, **kwargs):
    if created:
        subject = f"New post: {instance.title}"
        from_email = 'bidemia02@gmail.com'
        recipient_list = [user.email for user in User.objects.filter(profile__newsletter_opt_in=True)]

        html_content = render_to_string('emails/new_post.html', {'post': instance})
        text_content = instance.body[:200] + '...'

        msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
