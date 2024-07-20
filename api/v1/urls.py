from django.urls import path, include
from api.v1.authentication import urls as urls_autenticacion
from api.v1.ticket import urls as urls_tickets
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

urlpatterns = [
    path('autenticacion/', include(urls_autenticacion)),
    path('ticket/', include(urls_tickets)),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
