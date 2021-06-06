from datetime import datetime

from importlib import import_module
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer, TokenVerifySerializer

from .models import UserSession

SessionStore = import_module(settings.SESSION_ENGINE).SessionStore


# 미들웨어는 모든 호출에 대해서 다 호출이 되는데 그러면 안됨
# flag가 있어야 하고 그게 models.py에서 만든 is_user_logged_id가 되는 것
class KickMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        is_user_logged_in = getattr(request.user, 'is_user_logged_in', False)
        if is_user_logged_in:
            for user_session in UserSession.objects.filter(user=request.user):
                session_key = user_session.session_key
                session = SessionStore(session_key)
                # session.delete()
                session['kicked'] = True
                session.save()
                user_session.delete()  # 예전 로그인 세션 삭제

            session_key = request.session.session_key
            UserSession.objects.create(user=request.user, session_key=session_key)

        return response


# 중복 로그인 메세지 알림
class KickedMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # 현재 세션의 'kicked'가 True면 메세지를 띄우고 로그아웃한다.
        kicked = request.session.pop('kicked', None)
        if kicked:
            messages.info(request, '동일 아이디로 다른 브라우저 웹사이트에서 로그인이 감지되어, 강제 로그아웃 되었습니다.')
            auth_logout(request)
            return redirect(settings.LOGIN_URL)


# refresh jwt
class RefreshJWT(MiddlewareMixin):
    def process_response(self, request, response):
        # token을 발급받았는지 확인
        if 'jwt' in request.COOKIES:
            # access token verify
            # verify 포맷 맞춰주기
            attrs = {'token': request.COOKIES['jwt']}
            try:
                TokenVerifySerializer.validate(self, attrs=attrs)

            # access token이 invalid 할 경우
            except TokenError:
                try:
                    data = TokenRefreshSerializer.validate(self, attrs=request.COOKIES)
                # refresh token도 invalid할 경우
                except Exception as error:
                    messages.info(request, '토큰이 만료되었습니다.')
                    # 토큰 쿠키에서 삭제
                    if 'jwt' in request.COOKIES:
                        response.delete_cookie('jwt')
                    if 'refresh' in request.COOKIES:
                        response.delete_cookie('refresh')
                    return response

                # refresh token은 valid할 경우
                access = data['access']
                refresh = data['refresh']

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
                return response
            # 그 외 오류일 경우
            except Exception as e:
                print(e)
                messages.info(request, '오류가 발생하였습니다. 토큰을 다시 발급받아주십시오.')
                # 토큰 쿠키에서 삭제
                if 'jwt' in request.COOKIES:
                    response.delete_cookie('jwt')
                if 'refresh' in request.COOKIES:
                    response.delete_cookie('refresh')
                return response

        # token이 없는 경우
        return response
