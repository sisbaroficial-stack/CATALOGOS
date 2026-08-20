from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.template.defaultfilters import slugify

User = get_user_model()


class Album(models.Model):
    nombre = models.CharField(max_length=140)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    color = models.CharField(max_length=7, default='#0d6efd')
    orden = models.PositiveIntegerField(default=0, db_index=True)
    visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['orden', 'nombre', 'id']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    album = models.ForeignKey(Album, on_delete=models.PROTECT, related_name='productos')
    nombre = models.CharField(max_length=180)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    mostrar_stock = models.BooleanField(default=True)
    visible = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0, db_index=True)
    video = models.FileField(upload_to='productos/videos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['orden', 'nombre', 'id']

    def __str__(self):
        return self.nombre

    @property
    def imagen_principal(self):
        principal = self.imagenes.filter(es_principal=True).first()
        if principal:
            return principal.imagen
        primera = self.imagenes.order_by('orden', 'created_at').first()
        if primera:
            return primera.imagen
        return None

    @property
    def imagenes_ordenadas(self):
        return self.imagenes.order_by('orden', 'created_at')


class ProductoImagen(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='productos/')
    orden = models.PositiveIntegerField(default=0)
    es_principal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['orden', 'created_at']

    def save(self, *args, **kwargs):
        if self.es_principal:
            ProductoImagen.objects.filter(producto=self.producto, es_principal=True).exclude(pk=self.pk).update(es_principal=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.producto.nombre} - imagen {self.id}'


class ConfiguracionCatalogo(models.Model):
    nombre_negocio = models.CharField(max_length=180, default='Mi Catálogo')
    descripcion_publica = models.TextField(blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    color_primario = models.CharField(max_length=7, default='#0d6efd')
    mostrar_precios = models.BooleanField(default=True)
    mostrar_albumes = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='branding/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración del catálogo'
        verbose_name_plural = 'Configuración del catálogo'

    def __str__(self):
        return self.nombre_negocio

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
