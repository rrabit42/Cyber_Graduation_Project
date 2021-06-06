from celery import shared_task
from django.core.mail import  send_mail
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template import loader

UserModel = get_user_model()

# 가입 메일 보내기
@shared_task
def signup_mail(subject, message, sender, receivers):
    send_mail(subject, message, sender, receivers)


# password reset 이메일
@shared_task
def password_mail(subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
    subject = loader.render_to_string(subject_template_name, context)
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    body = loader.render_to_string(email_template_name, context)

    email_message = EmailMultiAlternatives(subject, body, from_email, [to_email])
    if html_email_template_name is not None:
        html_email = loader.render_to_string(html_email_template_name, context)
        email_message.attach_alternative(html_email, 'text/html')

    email_message.send()
