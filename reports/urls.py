from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.index, name='index'),
    path('download-mentorship-report-csv/', views.download_mentorship_report_csv, name='download_mentorship_report_csv'),
]