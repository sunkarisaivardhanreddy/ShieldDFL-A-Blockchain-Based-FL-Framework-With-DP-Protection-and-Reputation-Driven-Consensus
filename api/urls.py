from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('devices/', views.api_devices, name='devices'),
    path('rounds/', views.api_rounds, name='rounds'),
    path('upload-update/', views.api_upload_update, name='upload_update'),
]
