import json
from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import models, transaction
from django.db.models import Count, Max, Prefetch
from django.db.models.deletion import ProtectedError
from django.http import Http404, HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import AlbumForm, ConfiguracionCatalogoForm, ProductoForm
from .models import Album, ConfiguracionCatalogo, Producto, ProductoImagen


def _config():
    return ConfiguracionCatalogo.get_solo()


def pwa_manifest(request):
    config = _config()
    manifest = {
        'name': config.nombre_negocio or 'Catálogo',
        'short_name': (config.nombre_negocio or 'Catálogo')[:24],
        'start_url': '/',
        'display': 'standalone',
        'background_color': '#ffffff',
        'theme_color': config.color_primario or '#0d6efd',
        'icons': [{'src': '/static/catalogo/icon.svg', 'sizes': 'any', 'type': 'image/svg+xml'}],
    }
    return HttpResponse(json.dumps(manifest), content_type='application/manifest+json')


def pwa_service_worker(request):
    script = """const CACHE = 'catalogo-shell-v2';
const ASSETS = ['/', '/static/catalogo/css/catalogo.css', '/static/catalogo/js/catalogo.js', '/static/catalogo/icon.svg'];
self.addEventListener('install', event => event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS))));
self.addEventListener('activate', event => event.waitUntil(
  caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim())
));
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  event.respondWith(fetch(event.request).then(response => {
    const copy = response.clone();
    caches.open(CACHE).then(cache => cache.put(event.request, copy));
    return response;
  }).catch(() => caches.match(event.request).then(cached => cached || caches.match('/'))));
});"""
    response = HttpResponse(script, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    return response


def _is_admin(user):
    return user.is_authenticated and user.is_staff


def _whatsapp_digits(value):
    digits = ''.join(ch for ch in (value or '') if ch.isdigit())
    if digits.startswith('00'):
        digits = digits[2:]
    if digits.startswith('0'):
        digits = digits.lstrip('0')
    return digits


def _whatsapp_url(number, message):
    digits = _whatsapp_digits(number)
    if not digits:
        return ''
    return f'https://wa.me/{digits}?text={quote(message)}'


def _placeholder_image():
    return (
        'data:image/svg+xml;utf8,'
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="900" viewBox="0 0 1200 900">'
        '<defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="1"><stop offset="0%" stop-color="#0d6efd"/><stop offset="100%" stop-color="#7c3aed"/></linearGradient></defs>'
        '<rect width="1200" height="900" fill="url(#g)"/>'
        '<circle cx="240" cy="180" r="120" fill="rgba(255,255,255,.12)"/>'
        '<circle cx="980" cy="150" r="160" fill="rgba(255,255,255,.10)"/>'
        '<rect x="210" y="250" width="780" height="360" rx="42" fill="rgba(255,255,255,.16)"/>'
        '<text x="50%" y="50%" fill="#fff" font-family="Arial, sans-serif" font-size="56" font-weight="700" text-anchor="middle">Sin imagen disponible</text>'
        '</svg>'
    )


def _decorate_producto(producto, request=None):
    imagen = producto.imagen_principal
    producto.imagen_principal_url = imagen.url if imagen else ''
    producto.imagen_principal_placeholder = _placeholder_image()
    product_url = reverse('producto_detalle', kwargs={'producto_id': producto.id})
    if request:
        product_url = request.build_absolute_uri(product_url)
    producto.whatsapp_url = _whatsapp_url(
        _config().whatsapp,
        f'Hola, me gustaría comprar el producto “{producto.nombre}”. ¿Me confirmas disponibilidad y cómo puedo pedirlo?\n\nLink del producto: {product_url}',
    )
    return producto


def catalogo_publico(request):
    config = _config()
    if not config.activo:
        return render(request, 'catalogo/catalogo_inactivo.html', {'config': config})

    busqueda = request.GET.get('q', '').strip()
    album_id = request.GET.get('album', '').strip()
    vista = request.GET.get('vista', 'tarjetas')
    vista = vista if vista in {'tarjetas', 'lista'} else 'tarjetas'
    try:
        page_size = int(request.GET.get('page_size', 20))
    except ValueError:
        page_size = 20
    page_size = page_size if page_size in {20, 50, 100} else 20
    albums = (
        Album.objects.filter(visible=True)
        .annotate(productos_visibles_count=Count('productos', filter=models.Q(productos__visible=True), distinct=True))
        .prefetch_related(
            Prefetch(
                'productos',
                queryset=Producto.objects.filter(visible=True).prefetch_related('imagenes').order_by('orden', 'nombre'),
            )
        )
        .order_by('orden', 'nombre')
    )
    productos = Producto.objects.filter(visible=True).select_related('album').prefetch_related('imagenes')
    if busqueda:
        productos = productos.filter(
            models.Q(nombre__icontains=busqueda) | models.Q(descripcion__icontains=busqueda)
        )
    if album_id.isdigit():
        productos = productos.filter(album_id=album_id)
    productos = productos.order_by('orden', 'nombre')
    page_obj = Paginator(productos, page_size).get_page(request.GET.get('page'))
    productos = [_decorate_producto(producto, request) for producto in page_obj.object_list]
    albums_list = []
    for album in albums:
        album.productos_lista = [_decorate_producto(producto, request) for producto in album.productos.all()]
        albums_list.append(album)
    query_params = request.GET.copy()
    query_params.pop('page', None)

    return render(
        request,
        'catalogo/catalogo_publico.html',
        {
            'config': config,
            'albums': albums_list,
            'productos': productos,
            'busqueda': busqueda,
            'album_seleccionado': album_id,
            'vista': vista,
            'page_size': page_size,
            'page_obj': page_obj,
            'query_string': query_params.urlencode(),
            'whatsapp_url_global': _whatsapp_url(config.whatsapp, f'Hola, vi tu catálogo y me gustaría obtener más información.'),
        },
    )


def producto_detalle(request, producto_id):
    config = _config()
    producto = get_object_or_404(Producto.objects.select_related('album').prefetch_related('imagenes'), pk=producto_id, visible=True, album__visible=True)
    producto = _decorate_producto(producto, request)
    imagenes = list(producto.imagenes.order_by('orden', 'created_at'))
    imagen_principal = producto.imagen_principal_url or _placeholder_image()
    return render(
        request,
        'catalogo/producto_detalle.html',
        {
            'config': config,
            'producto': producto,
            'imagenes': imagenes,
            'imagen_principal': imagen_principal,
            'whatsapp_url_global': _whatsapp_url(config.whatsapp, f'Hola, me interesa el producto {producto.nombre}.'),
        },
    )


@login_required(login_url='/panel/login/')
@user_passes_test(_is_admin, login_url='/panel/login/')
def panel_dashboard(request):
    config = _config()
    if request.method == 'POST':
        form = ConfiguracionCatalogoForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configuración actualizada.')
            return redirect('panel_dashboard')
    else:
        form = ConfiguracionCatalogoForm(instance=config)

    albums = Album.objects.annotate(productos_count=Count('productos')).prefetch_related('productos').order_by('orden', 'nombre')
    busqueda_admin = request.GET.get('q', '').strip()
    productos_query = Producto.objects.select_related('album').prefetch_related('imagenes')
    if busqueda_admin:
        productos_query = productos_query.filter(
            models.Q(nombre__icontains=busqueda_admin)
            | models.Q(descripcion__icontains=busqueda_admin)
            | models.Q(album__nombre__icontains=busqueda_admin)
        )
    productos = [_decorate_producto(producto) for producto in productos_query.order_by('orden', 'nombre')]
    albums = list(albums)
    for album in albums:
        album.productos_lista = [_decorate_producto(producto) for producto in album.productos.all()]
        album.productos_count = len(album.productos_lista)
    return render(
        request,
        'catalogo/admin_dashboard.html',
        {
            'config_form': form,
            'config': config,
            'albums': albums,
            'productos': productos,
            'busqueda_admin': busqueda_admin,
            'album_form': AlbumForm(),
            'producto_form': ProductoForm(),
        },
    )


@login_required(login_url='/panel/login/')
@user_passes_test(_is_admin, login_url='/panel/login/')
def album_crear(request):
    form = AlbumForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Álbum creado.')
        return redirect('panel_dashboard')
    return render(request, 'catalogo/album_form.html', {'form': form, 'mode': 'Crear'})


@login_required(login_url='/panel/login/')
@user_passes_test(_is_admin, login_url='/panel/login/')
def album_editar(request, album_id):
    album = get_object_or_404(Album, pk=album_id)
    form = AlbumForm(request.POST or None, instance=album)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Álbum actualizado.')
        return redirect('panel_dashboard')
    return render(request, 'catalogo/album_form.html', {'form': form, 'mode': 'Editar', 'album': album})


@login_required(login_url='/panel/login/')
@user_passes_test(_is_admin, login_url='/panel/login/')
def album_eliminar(request, album_id):
    album = get_object_or_404(Album, pk=album_id)
    if request.method == 'POST':
        try:
            album.delete()
            messages.success(request, 'Álbum eliminado.')
        except ProtectedError:
            messages.error(request, 'No se puede eliminar un álbum con productos asociados. Oculátalo o mueve sus productos antes.')
        return redirect('panel_dashboard')
    return render(request, 'catalogo/confirm_delete.html', {'object': album, 'tipo': 'álbum'})


@login_required(login_url='/panel/login/')
@user_passes_test(_is_admin, login_url='/panel/login/')
def album_toggle_visible(request, album_id):
    album = get_object_or_404(Album, pk=album_id)
    if request.method != 'POST':
        raise Http404
    album.visible = not album.visible
    album.save(update_fields=['visible'])
    messages.success(request, f'Álbum {"visible" if album.visible else "oculto"}.')
    return redirect(request.META.get('HTTP_REFERER') or reverse('panel_dashboard'))


@login_required(login_url='/panel/login/')
@user_passes_test(_is_admin, login_url='/panel/login/')
def producto_crear(request):
    siguiente_orden = (Producto.objects.aggregate(max_orden=Max('orden'))['max_orden'] or 0) + 1
    form = ProductoForm(request.POST or None, request.FILES or None, initial={'orden': siguiente_orden})
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            producto = form.save()
            for index, archivo in enumerate(request.FILES.getlist('imagenes')):
                ProductoImagen.objects.create(producto=producto, imagen=archivo, orden=index, es_principal=index == 0)
        messages.success(request, 'Producto creado.')
        return redirect('panel_dashboard')
    return render(request, 'catalogo/producto_form.html', {'form': form, 'mode': 'Crear'})


@login_required(login_url='/panel/login/')
@user_passes_test(_is_admin, login_url='/panel/login/')
def producto_editar(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    form = ProductoForm(request.POST or None, request.FILES or None, instance=producto)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            producto = form.save()
            nuevas = request.FILES.getlist('imagenes')
            if nuevas:
                orden_base = producto.imagenes.count()
                for offset, archivo in enumerate(nuevas, start=1):
                    ProductoImagen.objects.create(producto=producto, imagen=archivo, orden=orden_base + offset, es_principal=False)
        messages.success(request, 'Producto actualizado.')
        return redirect('panel_dashboard')
    return render(
        request,
        'catalogo/producto_form.html',
        {'form': form, 'mode': 'Editar', 'producto': producto, 'imagenes': producto.imagenes.all()},
    )


@login_required(login_url='/panel/login/')
@user_passes_test(_is_admin, login_url='/panel/login/')
def producto_eliminar(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado.')
        return redirect('panel_dashboard')
    return render(request, 'catalogo/confirm_delete.html', {'object': producto, 'tipo': 'producto'})


@login_required(login_url='/panel/login/')
@user_passes_test(_is_admin, login_url='/panel/login/')
def producto_toggle_visible(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    if request.method != 'POST':
        raise Http404
    producto.visible = not producto.visible
    producto.save(update_fields=['visible'])
    messages.success(request, f'Producto {"visible" if producto.visible else "oculto"}.')
    return redirect(request.META.get('HTTP_REFERER') or reverse('panel_dashboard'))


@login_required(login_url='/panel/login/')
@user_passes_test(_is_admin, login_url='/panel/login/')
def producto_imagenes_subir(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    if request.method == 'POST':
        archivos = request.FILES.getlist('imagenes')
        if not archivos:
            messages.error(request, 'Selecciona al menos una imagen.')
            return redirect('producto_editar', producto_id=producto.id)
        if producto.imagenes.count() + len(archivos) > 4:
            messages.error(request, 'Cada producto admite máximo 4 imágenes.')
            return redirect('producto_editar', producto_id=producto.id)
        orden_base = producto.imagenes.count()
        for offset, archivo in enumerate(archivos, start=1):
            ProductoImagen.objects.create(producto=producto, imagen=archivo, orden=orden_base + offset, es_principal=False)
        messages.success(request, 'Imágenes subidas.')
    return redirect('producto_editar', producto_id=producto.id)


@login_required(login_url='/panel/login/')
@user_passes_test(_is_admin, login_url='/panel/login/')
def producto_video_subir(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    if request.method != 'POST':
        raise Http404
    video = request.FILES.get('video')
    if not video:
        messages.error(request, 'Selecciona un video para subir.')
    elif video.size > 25 * 1024 * 1024:
        messages.error(request, 'El video no puede superar 25 MB.')
    elif video.content_type not in {'video/mp4', 'video/webm', 'video/quicktime'}:
        messages.error(request, 'El video debe ser MP4, WebM o MOV.')
    else:
        producto.video = video
        producto.save(update_fields=['video'])
        messages.success(request, 'Video actualizado. Verifica que su duración no supere 10 segundos.')
    return redirect('producto_editar', producto_id=producto.id)


@login_required(login_url='/panel/login/')
@user_passes_test(_is_admin, login_url='/panel/login/')
def producto_imagen_eliminar(request, imagen_id):
    imagen = get_object_or_404(ProductoImagen, pk=imagen_id)
    producto_id = imagen.producto_id
    if request.method == 'POST':
        principal = imagen.es_principal
        imagen.delete()
        if principal:
            siguiente = ProductoImagen.objects.filter(producto_id=producto_id).order_by('orden', 'created_at').first()
            if siguiente:
                siguiente.es_principal = True
                siguiente.save(update_fields=['es_principal'])
        messages.success(request, 'Imagen eliminada.')
    return redirect('producto_editar', producto_id=producto_id)


@login_required(login_url='/panel/login/')
@user_passes_test(_is_admin, login_url='/panel/login/')
def producto_imagen_principal(request, imagen_id):
    imagen = get_object_or_404(ProductoImagen, pk=imagen_id)
    if request.method == 'POST':
        imagen.es_principal = True
        imagen.save(update_fields=['es_principal'])
        messages.success(request, 'Imagen principal actualizada.')
    return redirect('producto_editar', producto_id=imagen.producto_id)


@login_required(login_url='/panel/login/')
@user_passes_test(_is_admin, login_url='/panel/login/')
def configuracion_editar(request):
    return redirect('panel_dashboard')


def panel_logout(request):
    logout(request)
    return redirect('panel_login')
