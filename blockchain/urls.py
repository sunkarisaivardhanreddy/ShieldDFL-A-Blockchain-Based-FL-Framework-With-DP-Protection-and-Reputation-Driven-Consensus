from django.urls import path
from . import views

app_name = 'blockchain'

urlpatterns = [
    path('', views.blockchain_overview, name='overview'),
    path('blocks/', views.block_list, name='block_list'),
    path('blocks/<int:block_index>/', views.block_detail, name='block_detail'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/create/', views.create_manual_transaction, name='create_transaction'),
    path('mine/', views.mine_block, name='mine_block'),
    path('mine/all-devices/', views.mine_all_devices, name='mine_all_devices'),
    path('mine/random/', views.mine_random_device, name='mine_random_device'),
    path('transactions/recent/', views.recent_transactions_api, name='recent_transactions_api'),
    path('stats/', views.blockchain_stats, name='stats'),
    path('verify/', views.verify_chain, name='verify_chain'),
]
