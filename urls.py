from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('manual-predict/', views.manual_predict_view, name='manual_predict'),
    path('batch-predict/', views.batch_predict_view, name='batch_predict'),
    path('analytics/', views.analytics_dashboard, name='analytics'),
    path('view-logs/', views.view_logs, name='view_logs'),
    path('delete-log/<str:filename>/', views.delete_log, name='delete_log'),
    path('download-log/<str:filename>/', views.download_log, name='download_log'),
    path('realtime-logs/', views.realtime_logs, name='realtime_logs'),
    path('realtime_logs/delete_all/', views.delete_all_realtime_logs, name='delete_all_realtime_logs'),
    path('realtime-analytics/', views.realtime_analytics_dashboard, name='realtime_analytics'),
    path('dashboard/', views.analytics_dashboard, name='analytics_dashboard'),
    path('batch-analytics/', views.batch_analytics_dashboard, name='batch_analytics'),


]
