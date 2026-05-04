from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter

app_name = 'federated_learning'

urlpatterns = [
    path('rounds/', views.round_list, name='round_list'),
    path('rounds/<uuid:round_id>/', views.round_detail, name='round_detail'),
    path('rounds/<uuid:round_id>/join/<uuid:device_id>/', views.join_round, name='join_round'),
    path('rounds/<uuid:round_id>/simulate/', views.simulate_round, name='simulate_round'),
    path('rounds/start/', views.start_new_round, name='start_round'),
    path('rounds/<uuid:round_id>/aggregate/', views.aggregate_round, name='aggregate_round'),
    # API endpoints
    path('api/rounds/<uuid:round_id>/updates/', views.api_round_updates, name='api_round_updates'),
    path('api/rounds/<uuid:round_id>/status/', views.api_round_status, name='api_round_status'),
]
