from django.urls import path
from . import views

urlpatterns = [
    path('dashboard-redirect/', views.dashboard_redirect, name='dashboard_redirect'),
    path('mentor-dashboard/', views.mentor_dashboard, name='mentor_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    # This path handles the list of all mentors 
    path('', views.mentor_list, name='mentor_list'),

    # <int:pk> means "capture an integer (pk, which stands for primary key/ID) from the URL"and pass it to the 'mentor_detail' view.
    path('<int:pk>/', views.mentor_detail, name='mentor_detail'), 
    path('<int:mentor_pk>/request/', views.request_mentorship, name='request_mentorship'),
    
    path('my-notifications/', views.my_notifications, name='my_notifications'),
    
    path('request/<int:request_pk>/accept/', views.accept_request, name='accept_request'),# Addresses for mentor actions on specific requests
    path('request/<int:request_pk>/decline/', views.decline_request, name='decline_request'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('mentee-dashboard/',views.mentee_dashboard, name='mentee_dashboard'),
    
    path('request/<int:request_pk>/schedule/', views.schedule_session, name='schedule_session'),

    # This pattern captures the request ID and the recipient user ID
    path('request/<int:request_pk>/message/<int:recipient_pk>/',views.message_thread, name='message_thread'),
    path('my-profile/', views.my_profile, name='my_profile'),
    path('request/<int:request_pk>/', views.mentorship_request_detail, name='mentorship_request_detail'),
    path('notifications/mark-read/<int:notification_pk>/', views.mark_notification_read_and_redirect, name='mark_notification_read_and_redirect'),
    path('session/<int:session_pk>/complete/', views.complete_session, name='complete_session'),
    path('session/<int:session_pk>/report/', views.generate_session_report, name='generate_session_report'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('session/<int:session_pk>/feedback/', views.provide_feedback, name='provide_feedback'),
    path('mentor/session/<int:session_pk>/complete/', views.mentor_complete_session, name='mentor_complete_session'),
    path('mentor/session/<int:session_pk>/evaluate/', views.mentor_evaluate_mentee, name='mentor_evaluate_mentee'),
]
