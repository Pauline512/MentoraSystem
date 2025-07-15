from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_resource, name='upload_resource'),
    path('download/<int:pk>/', views.download_resource, name='download_resource'),
]