import json

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework import status, mixins
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenViewBase

from accounts.models import User
from .filters import InfoFilter
from .models import certPage
from .serializers import AIinfoSerialilzer, UserSerializer, UserPatternSerializer


# API로 받은거 보여주기
class certPost(GenericViewSet, mixins.CreateModelMixin):
    queryset = certPage.objects.all().order_by('created_at')
    serializer_class = AIinfoSerialilzer
    # http_method_names = ['GET', 'POST', 'PUT']
    # permission_classes = []

    # 권한 설정해야하는데..ㅎㅎ
    def create(self, request, *args, **kwargs):
        # proxy에 로그인 기능이 없어서 user_id보고 직접 user 객체 연결해주기
        user_id = request.data['user']

        # string으로 온 정확도들을 lfoat으로 바꿔주기
        request.data['user'] = User.objects.get(username=user_id).pk
        request.data['mouse_prediction'] = float(request.data['mouse_prediction'])
        request.data['resource_prediction'] = float(request.data['resource_prediction'])

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        print("끝났다")    # 왜 이걸 넣으면 winError 10054 에러가 안날까..?
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


# 얘도 serializer로 할 필요 X
class certUpdate(GenericViewSet, mixins.UpdateModelMixin):
    queryset = certPage.objects.all().order_by('created_at')
    serializer_class = AIinfoSerialilzer

    @method_decorator(login_required(login_url='login'))
    @method_decorator(staff_member_required)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()    # certPage
        user = instance.user            # User

        # 바꿔줄 라벨
        new_label = self.request.POST.get('label_state')

        # 라벨 선택 안했을 시
        if new_label is None:
            messages.info(request, 'label을 선택해주세요.')
            return redirect('manager:certDetailView')

        # 처벌 여부 결정
        if user.username != new_label:
            if instance.type == 3:
                # 벌점 부과
                user.penalty = user.penalty + 1

                # 벌점이 임계치에 도달하면 계정 정지
                if user.penalty >= 2:
                    user.is_active = 0
                    user.penalty = 0
                    messages.info(request, '이상행위가 감지되어 해당 계정을 정지시켰습니다.')

            # 정지 권고
            elif instance.type == 2:
                user.is_active = 0
                messages.info(request, '이상행위가 감지되어 계정이 정지시켰습니다.')

        instance.label = new_label  # label 바꿔주기
        instance.done = 1           # done 바꿔주기

        # certPage 업데이트
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # User 업데이트
        serializer = UserSerializer(user, data={
            'penalty': user.penalty,
            'is_active': user.is_active,
        }, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return redirect('manager:certDetailView')


# 얘는 serializer로 할 필요 X. 나중에 리팩토링
class certDetailView(GenericViewSet, mixins.ListModelMixin):
    queryset = certPage.objects.all().order_by('created_at')
    serializer_class = AIinfoSerialilzer

    @method_decorator(login_required(login_url='login'))
    @method_decorator(staff_member_required)
    def list(self, request, *args, **kwargs):
        # queryset = self.filter_queryset(self.get_queryset())
        queryset = self.filter_queryset(certPage.objects.filter(Q(done=0)))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        # tuple orderedlist to str
        cnt_json = json.dumps(serializer.data)

        # json to list
        lists = json.loads(cnt_json)

        # list to dictionary
        context = {}
        for list in lists:
            context[list['id']] = list

        user_list = queryset
        info_filter = InfoFilter(request.GET, queryset=user_list)
        context['filter'] = info_filter

        # 중복 없이 user_id 가져오기
        context['users'] = User.objects.all().values_list('username', flat=True).distinct()
        return render(request, 'manager/main.html', context, status=status.HTTP_200_OK)


# 유저가 패턴 데이터를 주면 proxy로 보내기 -> 추후 클라이언트 분리되면 클라이언트가 할 작업
class toProxyView(APIView):

    def post(self, request, *args, **kwargs):
        print(request.data)
        return Response(status=status.HTTP_200_OK)


class TokenVerifyView(TokenViewBase):
    """
    Takes a token and indicates if it is valid.  This view provides no
    information about a token's fitness for a particular use.
    """
    serializer_class = serializers.TokenVerifySerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
            # raise InvalidToken(e.args[0])
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
