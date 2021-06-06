from django.urls import path

from .views import certPost, certDetailView, certUpdate, toProxyView

app_name ='manager'


info_post = certPost.as_view({
    'post': 'create',
})

detail = certDetailView.as_view({
    'get': 'list',
})

info_update = certUpdate.as_view({
    'post': 'partial_update',
})

urlpatterns = [
    path('', detail, name='certDetailView'),
    path('add/', info_post, name='certPost'),
    path('update/<pk>', info_update, name='certUpdate'),
    path('userpattern/', toProxyView.as_view(), name='toproxy'),
]