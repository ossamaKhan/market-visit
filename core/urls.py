from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),  # Django's own built-in admin, unrelated to our Admin Portal

    path('', RedirectView.as_view(pattern_name='login', permanent=False), name='home'),

    # Field agent portal: /field/login/, /field/dashboard/, /field/log-visit/, /field/visits/<id>/
    path('field/', include('accounts.urls')),
    path('field/', include('visits.urls')),

    # Management portal: /management/login/, /management/dashboard/, /management/visits/, ...
    path('management/', include('reports.urls')),

    # Admin Portal: /admin-portal/login/, /admin-portal/users/, /admin-portal/visits/, ...
    path('admin-portal/', include('admin_portal.urls')),
    path('admin-portal/', include('hierarchy.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
