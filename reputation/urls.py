from django.urls import path
from . import views

app_name = 'reputation'

urlpatterns = [
    path('', views.reputation_overview, name='overview'),
    path('device/<uuid:device_id>/', views.device_reputation_detail, name='device_detail'),
    path('device/<uuid:device_id>/recompute/', views.recompute_reputation, name='recompute'),
]
