from django.contrib import admin

from .models import Album, ConfiguracionCatalogo, Producto, ProductoImagen


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'orden', 'visible', 'created_at')
    list_editable = ('orden', 'visible')
    search_fields = ('nombre',)
    prepopulated_fields = {'slug': ('nombre',)}


class ProductoImagenInline(admin.TabularInline):
    model = ProductoImagen
    extra = 1
    max_num = 4
    validate_max = True
    fields = ('imagen', 'orden', 'es_principal')


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'album', 'precio', 'visible', 'orden', 'created_at')
    list_filter = ('visible', 'album')
    search_fields = ('nombre', 'descripcion')
    list_editable = ('visible', 'orden')
    inlines = [ProductoImagenInline]


@admin.register(ConfiguracionCatalogo)
class ConfiguracionCatalogoAdmin(admin.ModelAdmin):
    list_display = ('nombre_negocio', 'whatsapp', 'activo', 'mostrar_precios', 'mostrar_albumes')

    def has_add_permission(self, request):
        return not ConfiguracionCatalogo.objects.exists()
