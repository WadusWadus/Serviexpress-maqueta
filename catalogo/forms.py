from django import forms
from django.db.models import Q

from core.forms import FormularioConVersion, FormularioModelo, aplicar_estilos

from .models import Producto, Servicio, ServicioProducto


class ProductoForm(FormularioModelo):
    """HU13 · RF17 · El código se guarda en mayúsculas y no se repite (sin importar mayúsculas)."""

    class Meta:
        model = Producto
        fields = ["codigo", "descripcion", "unidad", "activo"]

    def clean_codigo(self):
        codigo = self.cleaned_data["codigo"].strip().upper()
        if Producto.objects.filter(codigo__iexact=codigo).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe un producto con ese código.")
        return codigo


class ServicioForm(FormularioConVersion):
    """HU12 · RF15"""

    class Meta:
        model = Servicio
        fields = ["nombre", "descripcion", "precio", "duracion_bloques", "activo"]
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 3})}
        help_texts = {"duracion_bloques": "Duración estimada en horas (referencial)."}


class ServicioProductoForm(forms.ModelForm):
    class Meta:
        model = ServicioProducto
        fields = ["producto", "cantidad"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        actual = self.instance.producto_id if self.instance.pk else None
        self.fields["producto"].queryset = Producto.objects.filter(Q(activo=True) | Q(pk=actual))
        self.fields["cantidad"].widget.attrs.update(step="0.01", min="0.01")
        aplicar_estilos(self)


ProductosDelServicioFormSet = forms.inlineformset_factory(
    Servicio, ServicioProducto, form=ServicioProductoForm, extra=3, can_delete=True,
)
