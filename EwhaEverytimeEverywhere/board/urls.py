from django.urls import path
from . import views

app_name ='board'

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('upload/', views.post_upload, name='post_upload'),
    path('<int:pk>', views.post_detail, name='post_detail'),
    path('<int:pk>/delete/', views.post_delete, name='post_delete'),
    path('<int:pk>/edit/', views.post_edit, name='post_edit'),
]