from django.urls import path
from . import views

urlpatterns = [
    path('popup_key/', views.KeyCreateView.as_view(), name='create_key'),
    path('popup_token/', views.TokenCreateView.as_view(), name='create_token'),

    path('signup/', views.signup, name='signup'),
    path('login/', views.OurLoginView.as_view(), name='login'),
    path('logout/', views.OurLogoutView, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit', views.profile_edit, name='profile_edit'),

    # 비밀번호 번경
    path('password_change/', views.MyPasswordChangeView.as_view(), name='password_change'),

    # 비밀번호 분실 시 이메일을 통한 재설정
    path('password_reset/', views.MyPasswordResetView.as_view(), name='password_reset'),
    path('reset/<uidb64>/<token>/', views.MyPasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # 이메일 통한 가입 인증
    path('activate/<slug:uidb64>/<slug:token>', views.activate_account, name='activate'),
]