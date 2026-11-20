from decimal import Decimal

from django import forms

from catalogo.models import Producto
from core.forms import MENSAJE_CONFLICTO, Formulario, FormularioModelo, aplicar_estilos
from core.validadores import normalizar_rut

from .models import Proveedor


class ProveedorForm(FormularioModelo):
    """HU15 · RF19"""

    class Meta:
        model = Proveedor
        fields = ["rut", "razon_social", "nombre_contacto", "telefono", "email", "rubro", "activo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rut"].widget.attrs["placeholder"] = "76123456-0"
        if self.instance.pk:
            self.fields["rut"].disabled = True

    def clean_rut(self):
        return normalizar_rut(self.cleaned_data["rut"])


class OrdenForm(Formulario):
    """HU16 · RF20"""

    proveedor = forms.ModelChoiceField(label="Proveedor", queryset=Proveedor.objects.filter(activo=True))
    observacion = forms.CharField(label="Observación", required=False, widget=forms.Textarea(attrs={"rows": 2}))


class LineaOrdenForm(forms.Form):
    producto = forms.ModelChoiceField(label="Producto", queryset=Producto.objects.activos(), required=False)
    cantidad = forms.DecimalField(label="Cantidad", required=False, max_digits=10, decimal_places=2,
                                  min_value=Decimal("0.01"),
                                  error_messages={"min_value": "La cantidad debe ser mayor que 0."})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cantidad"].widget.attrs.update(step="0.01", min="0.01")
        aplicar_estilos(self)

    def clean(self):
        datos = super().clean()
        if datos.get("producto") and not datos.get("cantidad"):
            self.add_error("cantidad", "Indique la cantidad del producto.")
        if datos.get("cantidad") and not datos.get("producto"):
            self.add_error("producto", "Elija el producto.")
        return datos


class BaseLineasOrdenFormSet(forms.BaseFormSet):
    def clean(self):
        if any(self.errors):
            return
        productos = [f.cleaned_data["producto"] for f in self.forms if f.cleaned_data.get("producto")]
        if not productos:
            raise forms.ValidationError("La orden debe tener al menos un producto.")
        repetidos = {p for p in productos if productos.count(p) > 1}
        if repetidos:
            raise forms.ValidationError(f"Producto repetido en la orden: {', '.join(p.codigo for p in repetidos)}.")

    def lineas(self):
        return [(f.cleaned_data["producto"], f.cleaned_data["cantidad"]) for f in self.forms if f.cleaned_data.get("producto")]


LineasOrdenFormSet = forms.formset_factory(LineaOrdenForm, formset=BaseLineasOrdenFormSet, extra=5)


class BuscarOrdenForm(Formulario):
    numero = forms.IntegerField(label="N° de la orden", min_value=1)


class RecepcionForm(Formulario):
    """HU18 · RF24, RF25 · Una cantidad por línea + productos agregados por código."""

    EXTRAS = 2

    observacion = forms.CharField(label="Observación", required=False, widget=forms.Textarea(attrs={"rows": 2}))
    confirmar = forms.BooleanField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, orden, **kwargs):
        super().__init__(*args, **kwargs)
        self.orden = orden
        self.lineas = list(orden.lineas.select_related("producto"))
        for linea in self.lineas:
            campo = forms.DecimalField(label=linea.producto.descripcion, min_value=Decimal("0"), max_digits=10,
                                       decimal_places=2, initial=linea.cantidad_pendiente,
                                       error_messages={"min_value": "La cantidad no puede ser negativa."})
            campo.widget.attrs.update({"class": "input w-full", "step": "0.01", "min": "0"})
            self.fields[f"cantidad_{linea.pk}"] = campo
        for i in range(1, self.EXTRAS + 1):
            self.fields[f"codigo_extra_{i}"] = forms.CharField(label=f"Código de producto adicional {i}", required=False,
                                                               widget=forms.TextInput(attrs={"class": "input w-full", "placeholder": "Código del producto"}))
            self.fields[f"cantidad_extra_{i}"] = forms.DecimalField(
                label=f"Cantidad adicional {i}", required=False, min_value=Decimal("0.01"), max_digits=10, decimal_places=2,
                widget=forms.NumberInput(attrs={"class": "input w-full", "step": "0.01", "placeholder": "Cantidad"}))

    def filas(self):
        return [(linea, self[f"cantidad_{linea.pk}"]) for linea in self.lineas]

    def filas_extra(self):
        return [(self[f"codigo_extra_{i}"], self[f"cantidad_extra_{i}"]) for i in range(1, self.EXTRAS + 1)]

    def cantidades(self):
        return {l.producto_id: self.cleaned_data[f"cantidad_{l.pk}"] or Decimal("0") for l in self.lineas}

    def extras(self):
        return [(self.cleaned_data[f"codigo_extra_{i}"], self.cleaned_data[f"cantidad_extra_{i}"])
                for i in range(1, self.EXTRAS + 1)]


class OrdenModificarForm(Formulario):
    """HU17 · RF21 · RNF23"""

    observacion = forms.CharField(label="Observación", required=False, widget=forms.Textarea(attrs={"rows": 2}))
    version_leida = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, orden, **kwargs):
        super().__init__(*args, **kwargs)
        self.orden = orden
        self.fields["observacion"].initial = orden.observacion
        self.fields["version_leida"].initial = orden.version

    def clean(self):
        datos = super().clean()
        if datos.get("version_leida") is not None and datos["version_leida"] != self.orden.version:
            raise forms.ValidationError(MENSAJE_CONFLICTO, code="conflicto_version")
        return datos
