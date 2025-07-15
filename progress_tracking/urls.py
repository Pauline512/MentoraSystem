from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'progress_tracking'

# API Router
router = DefaultRouter()
router.register(r'goals', views.GoalViewSet, basename='goal')
router.register(r'progress-entries', views.ProgressEntryViewSet, basename='progress-entry')

urlpatterns = [
    # Main dashboard
    path('', views.dashboard_view, name='dashboard'),

    # Goal management
    path('goals/', views.GoalListView.as_view(), name='goal_list'),
    path('goals/create/', views.GoalCreateView.as_view(), name='goal_create'), # <--- CORRECTED LINE
    path('goals/<int:pk>/', views.goal_detail_view, name='goal_detail'),
    path('goals/<int:pk>/edit/', views.GoalUpdateView.as_view(), name='goal_update'),
    path('goals/<int:pk>/delete/', views.GoalDeleteView.as_view(), name='goal_delete'),

    # Progress tracking
    path('progress/create/', views.ProgressEntryCreateView.as_view(), name='progress_create'),
    path('progress/<int:pk>/', views.ProgressEntryDetailView.as_view(), name='progress_detail'),

    # AJAX endpoints
    path('api/progress-chart/<int:goal_id>/', views.progress_chart_data, name='progress_chart_data'),

    # REST API endpoints
    path('api/', include(router.urls)),
]