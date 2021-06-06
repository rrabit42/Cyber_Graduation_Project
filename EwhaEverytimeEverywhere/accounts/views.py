from EwhaEverytimeEverywhere import settings

from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout, get_user_model, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordChangeView, \
    LoginView
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic import UpdateView

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.generators.token_generator import account_activation_token
from accounts.tasks import signup_mail, password_mail
from lib.bootstrap_modal_forms.generic import BSModalCreateView, BSModalFormView

from .forms import SignupForm, ProfileForm, KeyCreationForm, KeyAuthenticationForm
from .models import Profile, User, UserKeyToken


UserModel = get_user_model()


def EmailLoginView(request):
    form = AuthenticationForm()
    if request.method == "GET":
        return render(request, 'accounts/login.html', {'form': form})

    elif request.method == "POST":
        # 전송 받은 이메일, 비밀번호 확인
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 유효성 처리
        res_data = {}
        if not (username and password):
            messages.info(request, '이메일과 비밀번호를 모두 입력해주세요!')
        else:
            # DB와 비교 진행
            try:
                user = User.objects.get(email=username)
            except ObjectDoesNotExist:
                messages.info(request, '그런 유저는 읍따')
            else:
                # 비밀번호 확인
                if check_password(password, user.password):
                    # 세션 등 처리 위해...
                    auth_login(request, form.get_user())
                    # 리다이렉트
                    messages.info(request, '로그인 성공!')  # 여기에 user.typing_id를 주던데
                    return redirect('profile')
                else:
                    messages.info(request, '비밀번호를 틀리셨습니다.')

    return render(request, 'accounts/login.html', {'form': form})


class OurLoginView(LoginView):
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        """Security check complete. Log the user in."""
        # print(self.request.POST.get('username'))
        # print(self.request.POST.get('password'))
        try:
            auth_login(self.request, form.get_user())
        except Exception:
            messages.info(self.request, '틀렸습니다')
        return HttpResponseRedirect(self.get_success_url())

    def dispatch(self, *args, **kwargs):
        return super(OurLoginView, self).dispatch(*args, **kwargs)


def OurLogoutView(request):
    logout(request)
    response = redirect('login')
    if 'jwt' in request.COOKIES:
        response.delete_cookie('jwt')
    if 'refresh' in request.COOKIES:
        response.delete_cookie('refresh')
    return response


# 함수 기반 뷰
def signup(request):
    global user
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
            except Exception as e:
                messages.info(request, '다시 입력해주세요')
                return HttpResponseRedirect(reverse('signup'))

            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            email_subject = 'Activate Your Account'
            message = render_to_string('accounts/activate_account.html', {
                'protocol': 'https' if request.is_secure() else 'http',
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user)
            })
            to_email = form.cleaned_data.get('email')
            signup_mail.delay(email_subject, message, settings.EMAIL_HOST_USER, [to_email])
            messages.info(request, '이메일로 인증링크를 보냈습니다. 링크를 통해 계정 확인을 완료해주세요!')
            return HttpResponseRedirect(reverse('login'))
    else:
        form = SignupForm()
    return render(request, 'accounts/signup.html', {
        'form': form,
    })


# 이메일 인증
def activate_account(request, uidb64, token):
    try:
        uid = force_bytes(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        # login(request, user)
        messages.info(request, '계정이 활성화되었습니다! 이제 로그인을 통해 사이트를 이용하실 수 있습니다!')
        return render(request, 'accounts/login.html')
    else:
        return HttpResponseRedirect(reverse_lazy('root'))


# 가입 환영 메일(feat.signal)
def on_post_save_for_user(sender, **kwargs):
    if kwargs['created']:
        # 가입시기
        user = kwargs['instance']
        # Profile.objects.create(user=user)  # 과거: User가 만들어지고 나서 profile 만들어짐

        # 환영 이메일 보내기
        signup_mail.delay(
            '환영합니다',
            '안녕하세요! EEE page에 가입하신 것을 환영합니다.',
            'me@Ewha.kr',
            [user.email],
        )
        return None


post_save.connect(on_post_save_for_user, sender=settings.AUTH_USER_MODEL, weak=False)


# 프로필
@login_required
def profile(request):
    return render(request, 'accounts/profile.html')


# 프로필 수정
class ProfileUpdateView(UpdateView, LoginRequiredMixin):  # login_required 장식자의 CBV 버전인 LoginRequiredMixin
    model = Profile
    form_class = ProfileForm
    success_url = reverse_lazy('profile')

    def get_object(self):
        return self.request.user.profile


profile_edit = ProfileUpdateView.as_view()


# 비밀번호 변경
class MyPasswordChangeView(PasswordChangeView):
    success_url = reverse_lazy('profile')
    template_name = 'accounts/password_change_form.html'

    def form_valid(self, form):
        messages.info(self.request, '암호가 변경이 되었습니다.')
        return super().form_valid(form)


# 비밀번호 리셋
class MyPasswordResetView(PasswordResetView):
    success_url = reverse_lazy('login')
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'

    def form_valid(self, form):
        messages.info(self.request, '암호 변경 메일을 발송했습니다.')
        return super().form_valid(form)

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None,
             extra_email_context=None):
        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        email = self.cleaned_data["email"]
        email_field_name = UserModel.get_email_field_name()
        for user in self.get_users(email):
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            user_email = getattr(user, email_field_name)
            context = {
                'email': user_email,
                'domain': domain,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
                **(extra_email_context or {}),
            }
            password_mail.delay(
                subject_template_name, email_template_name, context, from_email,
                user_email, html_email_template_name=html_email_template_name,
            )


# 비밀번호 리셋 confirm
class MyPasswordResetConfirmView(PasswordResetConfirmView):
    success_url = reverse_lazy('login')
    template_name = 'accounts/password_reset_confirm.html'

    def form_valid(self, form):
        messages.info(self.request, '암호 재설정을 완료하였습니다.')
        return super().form_valid(form)


# key 발급
class KeyCreateView(BSModalCreateView):
    template_name = 'accounts/popup_create_key.html'
    form_class = KeyCreationForm
    success_message = 'key 발급 성공'
    success_url = reverse_lazy('root')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    @method_decorator(login_required(login_url='login'))
    @method_decorator(staff_member_required)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @method_decorator(login_required(login_url='login'))
    @method_decorator(staff_member_required)
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


# token 발급(프록시에서 할 일 같은데..)
class TokenCreateView(BSModalFormView):
    template_name = 'accounts/popup_create_token.html'
    form_class = KeyAuthenticationForm
    success_message = '토큰이 발급 되었습니다'

    def form_valid(self, form):
        user = self.request.user
        instance = UserKeyToken.objects.all()

        # 1. user 확인
        # print(user)
        # 로그인된 유저가 아닐 경우
        if not user.is_authenticated:
            messages.success(self.request, '잘못된 접근입니다.')
            return HttpResponseRedirect(self.get_success_url())  # 사실 success_url이 아닌데..ㅋㅋ

        # key를 발급 받지 않은 유저일 경우
        if not UserKeyToken.objects.filter(user=user):
            messages.success(self.request, 'key를 발급받지 않은 유저입니다.')
            return HttpResponseRedirect(self.get_success_url())

        # 2. key 확인
        key = form.cleaned_data['key']
        today = datetime.today()
        if not UserKeyToken.objects.filter(key=key, created_at__day=today.day):
            messages.success(self.request, '잘못된 key입니다.')
            return HttpResponseRedirect(self.get_success_url())

        # 3. jwt 발급
        jwt_serializer = TokenObtainPairSerializer()
        refresh = jwt_serializer.get_token(user=user)
        access = refresh.access_token

        # 이 토큰을 user(client)에게 줌
        # proxy는 알 필요 없음 그냥 verify 하면 됨!

        response = super().form_valid(form)

        # 쿠키 만료 시간
        access_exp = (datetime.now() + settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'])
        refresh_exp = (datetime.now() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'])

        response.set_cookie('jwt',
                            access,
                            expires=access_exp,
                            httponly=True)
        response.set_cookie('refresh',
                            refresh,
                            expires=refresh_exp,
                            httponly=True)

        success_message = self.get_success_message(form.cleaned_data)
        if success_message:
            messages.success(self.request, success_message)
        return response

    def get_success_message(self, cleaned_data):
        return self.success_message % cleaned_data

    def get_success_url(self):
        return reverse_lazy('root')


# jwt 발급
class JWTObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
