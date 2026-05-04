from django.urls import path
from . import views

app_name = 'privacy'

urlpatterns = [
    path('', views.privacy_overview, name='overview'),
    path('api/budgets/', views.privacy_budgets_api, name='budgets_api'),
    path('device/<uuid:device_id>/', views.device_privacy_detail, name='device_detail'),
    path('device/<uuid:device_id>/reset/', views.reset_device_privacy, name='reset'),
]
