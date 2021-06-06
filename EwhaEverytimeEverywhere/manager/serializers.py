from rest_framework import serializers

from accounts.models import User
from manager.models import certPage


class AIinfoSerialilzer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        help_text='유저',
        queryset=User.objects.all()
    )
    time = serializers.DateTimeField(
        help_text='모델이 판단한 시간'
    )
    mouse_prediction = serializers.FloatField(
        help_text='AI가 판단한 총 확률'
    )
    resource_prediction = serializers.FloatField(
        help_text='AI가 판단한 총 확률'
    )
    # total_prediction = serializers.CharField(
    #     help_text='AI가 판단한 총 확률'
    # )
    type = serializers.IntegerField(
        help_text='계정 비활성화:2 / 벌점: 3'
    )
    label = serializers.CharField(
        default=user.pk_field,
        help_text='label'
    )
    mouse_file_list = serializers.CharField(
        help_text='마우스 패턴 파일'
    )
    resource_file_list = serializers.CharField(
        help_text='리소스 패턴 파일'
    )

    class Meta:
        model = certPage
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class UserPatternSerializer(serializers.Serializer):
    user = serializers.CharField(
        help_text='사용자계정',
    )
    is_user_block = serializers.BooleanField(
        help_text='사용자계정 차단 여부',
    )
    mouse_file = serializers.FileField(
        help_text='사용자 마우스 패턴',
    )
    resource_file = serializers.FileField(
        help_text='사용자 리소스 패턴',
    )
    cookie_jwt = serializers.CharField(
        help_text='쿠키의 jwt',
    )

