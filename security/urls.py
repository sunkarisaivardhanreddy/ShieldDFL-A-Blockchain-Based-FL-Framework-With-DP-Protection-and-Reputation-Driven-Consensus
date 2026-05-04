from django.urls import path
from . import views

app_name = 'security'

urlpatterns = [
    path('', views.security_overview, name='overview'),
    path('sar/', views.sar_logs, name='sar_logs'),
    path('basr/', views.basr_logs, name='basr_logs'),
]
