from django import forms

from .models import Album, ConfiguracionCatalogo, Producto


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        attrs = attrs or {}
        attrs.setdefault('multiple', True)
        super().__init__(attrs)


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_clean(item, initial) for item in data if item]
        return single_clean(data, initial)


class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ['nombre', 'color', 'orden', 'visible']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductoForm(forms.ModelForm):
    imagenes = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={'class': 'form-control', 'accept': 'image/*', 'data-product-images': '1'}),
        help_text='Puedes subir hasta 4 imágenes por producto.'
    )
    video = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'video/mp4,video/webm,video/quicktime', 'data-product-video': '1'}),
        help_text='Video opcional de máximo 10 segundos.'
    )

    class Meta:
        model = Producto
        fields = ['album', 'nombre', 'descripcion', 'precio', 'stock', 'mostrar_stock', 'visible', 'orden', 'video']
        widgets = {
            'album': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'mostrar_stock': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

    def clean_imagenes(self):
        imagenes = self.cleaned_data.get('imagenes') or []
        if not isinstance(imagenes, list):
            imagenes = [imagenes]
        existentes = self.instance.imagenes.count() if self.instance and self.instance.pk else 0
        if existentes + len(imagenes) > 4:
            raise forms.ValidationError(f'Cada producto admite máximo 4 imágenes. Actualmente tiene {existentes}.')
        return imagenes

    def clean_video(self):
        video = self.cleaned_data.get('video')
        if video and video.size > 25 * 1024 * 1024:
            raise forms.ValidationError('El video no puede superar 25 MB.')
        return video


class ConfiguracionCatalogoForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionCatalogo
        fields = ['nombre_negocio', 'descripcion_publica', 'whatsapp', 'color_primario', 'mostrar_precios', 'mostrar_albumes', 'activo', 'logo']
        widgets = {
            'nombre_negocio': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion_publica': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 573001112233'}),
            'color_primario': forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
            'mostrar_precios': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mostrar_albumes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'logo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
