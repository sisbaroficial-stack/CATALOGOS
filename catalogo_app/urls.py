from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('catalogo.urls')),
]

# django.conf.urls.static.static() ignora rutas cuando DEBUG=False. Render usa
# DEBUG=False incluso al habilitar SERVE_MEDIA, por eso declaramos esta ruta de
# desarrollo/instancia única de forma explícita para los archivos subidos.
if settings.DEBUG or settings.SERVE_MEDIA:
    media_url_path = settings.MEDIA_URL.lstrip('/')
    urlpatterns += [
        re_path(
            rf'^{media_url_path}(?P<path>.*)$',
            serve,
            {'document_root': settings.MEDIA_ROOT},
        ),
    ]
