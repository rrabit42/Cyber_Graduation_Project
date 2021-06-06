from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms

from lib.bootstrap_modal_forms.forms import BSModalModelForm, BSModalForm

from .models import User, Profile, UserKeyToken


# UserCreationForm은 auth에 있는 폼 가져온거라
# auth.User로 지정이 되어있음
class SignupForm(UserCreationForm):
    # Profile 정보를 입력받고 싶으니
    # Profile Model에 있는 필드들 가져온다
    last_name = forms.CharField(required=True, help_text='성')
    first_name = forms.CharField(required=True, help_text='이름')
    info = forms.CharField(widget=forms.Textarea, required=False)
    sex = forms.RadioSelect()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        user = None
        try:
            user = super().save(commit=False)  # model필드(현재 모델 User)와 관련된 필드만 저장됨
            user.save()
        except Exception:
            user.delete()
            raise Exception

        info = self.cleaned_data.get('info', None)

        Profile.objects.create(user=user, info=info,) # user랑 profile이랑 1:1 관계라 user가 있어야 profile 만들 수 있음

        return user

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('sex', 'email', 'last_name', 'first_name')


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['info', ]  # user 추가하면 User도 수정할 수 있어서 절대 안됨


class KeyCreationForm(BSModalModelForm):
    key = forms.CharField(
        error_messages={'invalid': '유효한 key를 입력하세요.'}
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.all()
    )

    class Meta:
        model = UserKeyToken
        exclude = ('created_at', )


class KeyAuthenticationForm(BSModalForm):
    key = forms.CharField(
        error_messages={'invalid': '유효한 key를 입력하세요.'}
    )
