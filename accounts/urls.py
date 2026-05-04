from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('devices/', views.device_list_view, name='device_list'),
    path('devices/register/', views.device_register_view, name='device_register'),
    path('devices/<uuid:device_id>/', views.device_detail_view, name='device_detail'),
    path('devices/<uuid:device_id>/delete/', views.device_delete_view, name='device_delete'),
    path('devices/<uuid:device_id>/metrics/', views.device_metrics_api, name='device_metrics_api'),
]
