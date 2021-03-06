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
        # ?????? ?????? ?????????, ???????????? ??????
        username = request.POST.get('username')
        password = request.POST.get('password')

        # ????????? ??????
        res_data = {}
        if not (username and password):
            messages.info(request, '???????????? ??????????????? ?????? ??????????????????!')
        else:
            # DB??? ?????? ??????
            try:
                user = User.objects.get(email=username)
            except ObjectDoesNotExist:
                messages.info(request, '?????? ????????? ??????')
            else:
                # ???????????? ??????
                if check_password(password, user.password):
                    # ?????? ??? ?????? ??????...
                    auth_login(request, form.get_user())
                    # ???????????????
                    messages.info(request, '????????? ??????!')  # ????????? user.typing_id??? ?????????
                    return redirect('profile')
                else:
                    messages.info(request, '??????????????? ??????????????????.')

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
            messages.info(self.request, '???????????????')
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


# ?????? ?????? ???
def signup(request):
    global user
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
            except Exception as e:
                messages.info(request, '?????? ??????????????????')
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
            messages.info(request, '???????????? ??????????????? ???????????????. ????????? ?????? ?????? ????????? ??????????????????!')
            return HttpResponseRedirect(reverse('login'))
    else:
        form = SignupForm()
    return render(request, 'accounts/signup.html', {
        'form': form,
    })


# ????????? ??????
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
        messages.info(request, '????????? ????????????????????????! ?????? ???????????? ?????? ???????????? ???????????? ??? ????????????!')
        return render(request, 'accounts/login.html')
    else:
        return HttpResponseRedirect(reverse_lazy('root'))


# ?????? ?????? ??????(feat.signal)
def on_post_save_for_user(sender, **kwargs):
    if kwargs['created']:
        # ????????????
        user = kwargs['instance']
        # Profile.objects.create(user=user)  # ??????: User??? ??????????????? ?????? profile ????????????

        # ?????? ????????? ?????????
        signup_mail.delay(
            '???????????????',
            '???????????????! EEE page??? ???????????? ?????? ???????????????.',
            'me@Ewha.kr',
            [user.email],
        )
        return None


post_save.connect(on_post_save_for_user, sender=settings.AUTH_USER_MODEL, weak=False)


# ?????????
@login_required
def profile(request):
    return render(request, 'accounts/profile.html')


# ????????? ??????
class ProfileUpdateView(UpdateView, LoginRequiredMixin):  # login_required ???????????? CBV ????????? LoginRequiredMixin
    model = Profile
    form_class = ProfileForm
    success_url = reverse_lazy('profile')

    def get_object(self):
        return self.request.user.profile


profile_edit = ProfileUpdateView.as_view()


# ???????????? ??????
class MyPasswordChangeView(PasswordChangeView):
    success_url = reverse_lazy('profile')
    template_name = 'accounts/password_change_form.html'

    def form_valid(self, form):
        messages.info(self.request, '????????? ????????? ???????????????.')
        return super().form_valid(form)


# ???????????? ??????
class MyPasswordResetView(PasswordResetView):
    success_url = reverse_lazy('login')
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'

    def form_valid(self, form):
        messages.info(self.request, '?????? ?????? ????????? ??????????????????.')
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


# ???????????? ?????? confirm
class MyPasswordResetConfirmView(PasswordResetConfirmView):
    success_url = reverse_lazy('login')
    template_name = 'accounts/password_reset_confirm.html'

    def form_valid(self, form):
        messages.info(self.request, '?????? ???????????? ?????????????????????.')
        return super().form_valid(form)


# key ??????
class KeyCreateView(BSModalCreateView):
    template_name = 'accounts/popup_create_key.html'
    form_class = KeyCreationForm
    success_message = 'key ?????? ??????'
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


# token ??????(??????????????? ??? ??? ?????????..)
class TokenCreateView(BSModalFormView):
    template_name = 'accounts/popup_create_token.html'
    form_class = KeyAuthenticationForm
    success_message = '????????? ?????? ???????????????'

    def form_valid(self, form):
        user = self.request.user
        instance = UserKeyToken.objects.all()

        # 1. user ??????
        # print(user)
        # ???????????? ????????? ?????? ??????
        if not user.is_authenticated:
            messages.success(self.request, '????????? ???????????????.')
            return HttpResponseRedirect(self.get_success_url())  # ?????? success_url??? ?????????..??????

        # key??? ?????? ?????? ?????? ????????? ??????
        if not UserKeyToken.objects.filter(user=user):
            messages.success(self.request, 'key??? ???????????? ?????? ???????????????.')
            return HttpResponseRedirect(self.get_success_url())

        # 2. key ??????
        key = form.cleaned_data['key']
        today = datetime.today()
        if not UserKeyToken.objects.filter(key=key, created_at__day=today.day):
            messages.success(self.request, '????????? key?????????.')
            return HttpResponseRedirect(self.get_success_url())

        # 3. jwt ??????
        jwt_serializer = TokenObtainPairSerializer()
        refresh = jwt_serializer.get_token(user=user)
        access = refresh.access_token

        # ??? ????????? user(client)?????? ???
        # proxy??? ??? ?????? ?????? ?????? verify ?????? ???!

        response = super().form_valid(form)

        # ?????? ?????? ??????
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


# jwt ??????
class JWTObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
