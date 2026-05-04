from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.user_dashboard, name='user_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/sync-devices/', views.sync_devices_view, name='sync_devices'),
    
    # User Management URLs
    path('admin/users/', views.user_management_list, name='user_management'),
    path('admin/users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('admin/users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('admin/users/<int:user_id>/toggle/', views.user_toggle_status, name='user_toggle_status'),
    path('admin/users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
]
