from django.db import models
from django.conf import settings


class certPage(models.Model):
    # 하나의 user의 여러개의 certPage
    # 원래는 proxy에서 로그인한 계정(proxy에 로그인 기능 없으니까 user_id 줌)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, editable=False)

    time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    mouse_prediction = models.FloatField(max_length=5)
    resource_prediction = models.FloatField(max_length=5)
    # total_prediction = models.CharField(max_length=5)
    type = models.IntegerField(default=1)   # 계정 비활성화(차단): 2 / 벌점: 3
    label = models.CharField(max_length=15) # cert팀에서 수정 가능한 label
    done = models.BooleanField(default=0)   # 0: 아직 cert팀 확인 전, 1: cert팀 확인 후

    mouse_file_list = models.TextField()    # ,로 split
    resource_file_list = models.TextField() # ,로 split

    def __str__(self):
        return self.user.username

