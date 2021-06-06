from __future__ import absolute_import
import os
from celery import Celery

from EwhaEverytimeEverywhere import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EwhaEverytimeEverywhere.settings')

app = Celery('practice'
             # broker=[
             #     'redis://redis',
             #     'redis://localhost'
             # ]
             )

# 문자열로 등록은 Celery Worker가 자식 프로세스에게 피클링하지 하지 않아도 되다고 알림
# namespace = 'CELERY'는 Celery관련 세팅 파일에서 변수 Prefix가 CELERY_ 라고 알림
app.config_from_object('django.conf:settings', namespace='CELERY')
# app.conf.broker_transport_options = {
#      'max_retries': 3,
#      'interval_start': 0,
#      'interval_step': 0.2,
#      'interval_max': 0.2,
# }

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))