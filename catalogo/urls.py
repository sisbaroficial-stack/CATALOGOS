from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('manifest.webmanifest', views.pwa_manifest, name='pwa_manifest'),
    path('service-worker.js', views.pwa_service_worker, name='pwa_service_worker'),
    path('', views.catalogo_publico, name='catalogo_publico'),
    path('producto/<int:producto_id>/', views.producto_detalle, name='producto_detalle'),
    path('panel/login/', auth_views.LoginView.as_view(template_name='catalogo/admin_login.html'), name='panel_login'),
    path('panel/logout/', views.panel_logout, name='panel_logout'),
    path('panel/', views.panel_dashboard, name='panel_dashboard'),
    path('panel/producto/nuevo/', views.producto_crear, name='producto_crear'),
    path('panel/producto/<int:producto_id>/editar/', views.producto_editar, name='producto_editar'),
    path('panel/producto/<int:producto_id>/eliminar/', views.producto_eliminar, name='producto_eliminar'),
    path('panel/producto/<int:producto_id>/toggle-visible/', views.producto_toggle_visible, name='producto_toggle_visible'),
    path('panel/producto/<int:producto_id>/imagenes/subir/', views.producto_imagenes_subir, name='producto_imagenes_subir'),
    path('panel/producto/<int:producto_id>/video/subir/', views.producto_video_subir, name='producto_video_subir'),
    path('panel/producto/imagen/<int:imagen_id>/eliminar/', views.producto_imagen_eliminar, name='producto_imagen_eliminar'),
    path('panel/producto/imagen/<int:imagen_id>/principal/', views.producto_imagen_principal, name='producto_imagen_principal'),
    path('panel/album/nuevo/', views.album_crear, name='album_crear'),
    path('panel/album/<int:album_id>/editar/', views.album_editar, name='album_editar'),
    path('panel/album/<int:album_id>/eliminar/', views.album_eliminar, name='album_eliminar'),
    path('panel/album/<int:album_id>/toggle-visible/', views.album_toggle_visible, name='album_toggle_visible'),
    path('panel/configuracion/', views.configuracion_editar, name='configuracion_editar'),
]
