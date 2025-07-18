from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.index, name='index'),
    path('unified-report/', views.unified_report_view, name='unified_report'),
]