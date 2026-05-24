"""Pantry Nova URL Configuration."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView


handler404 = 'accounts.views.page_not_found'


urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('admin/', include('admin_panel.urls')),
    path('manager/', include('managers.urls')),
    path('member/', include('members.urls')),
    path('chatbot/', include('chatbot.urls')),
    path('', include('subscriptions.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
