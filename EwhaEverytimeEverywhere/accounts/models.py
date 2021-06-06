from importlib import import_module

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as AuthUserManager
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.http import Http404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


class UserManager(AuthUserManager):
    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault('sex', 'm')
        extra_fields.setdefault('is_active', True)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    # email = models.EmailField(_('email address'), unique=True)
    is_active = models.BooleanField(default=False)
    sex = models.CharField(
        max_length=1,
        choices=(
            ('f', 'female'),
            ('m', 'male')
        ),
        verbose_name='성별'
    )
    penalty = models.IntegerField(
        default=0,
        verbose_name='벌점'
    )

    objects = UserManager()
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    def __str__(self):
        return self.username


class UserSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, editable=False)
    session_key = models.CharField(max_length=40, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)


# 중복 로그인 방지
# user_logged_in 시그널에 기존에 로그인한 세션을 삭제해주는 리시버를 연결
def kicked_my_other_sessions(sender, request, user, **kwargs):
    print('kicked my other sessions')

    # 이전에 생성된 세션이 있을 경우 삭제
    for user_session in UserSession.objects.filter(user=user):
        session_key = user_session.session_key
        session = SessionStore(session_key)
        # session.delete() 메세지 보내기 위해 주석처리
        session['kicked'] = True
        session.save()
        user_session.delete()

    if not request.session.session_key:
        request.session.create()

    # 현제 세션에 대한 레코드를 생성하여 저장
    session_key = request.session.session_key
    UserSession.objects.create(user=user, session_key=session_key)

user_logged_in.connect(kicked_my_other_sessions)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    info = models.TextField(blank=True)


class RestrictStaffToAdminMiddleware(object):
    """
    A middleware that restricts staff members access to administration panels.
    """
    def process_request(self, request):
        if request.path.startswith(reverse('admin:index')):
            if request.user.is_authenticated():
                if not request.user.is_staff:
                    raise Http404
            else:
                raise Http404


# User Key (Token 발급 위함)
class UserKeyToken(models.Model):
    key = models.CharField(max_length=30)
    # token = models.CharField(max_length=30, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)    # 발급 시간


