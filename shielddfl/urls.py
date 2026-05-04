from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('accounts/', include('accounts.urls')),
    path('federated-learning/', include('federated_learning.urls')),
    path('blockchain/', include('blockchain.urls')),
    path('reputation/', include('reputation.urls')),
    path('privacy/', include('privacy.urls')),
    path('security/', include('security.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('api/', include('api.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "ShieldDFL Administration"
admin.site.site_title = "ShieldDFL Admin Portal"
admin.site.index_title = "Welcome to ShieldDFL Administration"
