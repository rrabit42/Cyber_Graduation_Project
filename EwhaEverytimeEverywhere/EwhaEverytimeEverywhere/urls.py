from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from rest_framework_simplejwt.views import TokenVerifyView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', TemplateView.as_view(template_name='index.html'), name='root'),
    path('accounts/', include('accounts.urls')),
    path('blog/', include('board.urls')),
    path('main/', include('manager.urls')),

    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('ckeditor/', include('ckeditor_uploader.urls'))
]

# debug true일 때만 static file 작동
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)