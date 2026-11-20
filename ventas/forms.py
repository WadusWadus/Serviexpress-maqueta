from django import forms

from core.forms import MENSAJE_CONFLICTO, Formulario
from core.validadores import normalizar_rut, validar_rut


class ServiciosField(forms.ModelMultipleChoiceField):
    widget = forms.CheckboxSelectMultiple

    def label_from_instance(self, obj):
        return f"{obj.servicio.nombre} · {obj.fecha:%d-%m-%Y} · {obj.empleado.nombre_completo}"


class EmitirBoletaForm(Formulario):
    """HU19 · RF26 · Paso 2: marcar los servicios pendientes."""

    servicios = ServiciosField(label="Servicios pendientes", queryset=None,
                               error_messages={"required": "Marque al menos un servicio."})
    observacion = forms.CharField(label="Observación", required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, pendientes, cliente=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["servicios"].queryset = pendientes
        if cliente is not None and cliente.fiado_habilitado:
            # HU07 · La casilla aparece solo si el cliente está habilitado (HU06).
            self.fields["fiada"] = forms.BooleanField(label="Venta fiada", required=False,
                                                      help_text="El total se suma al saldo de fiado del cliente.")
            self.fields["fiada"].widget.attrs["class"] = "checkbox checkbox-warning checkbox-sm"


class FacturaForm(EmitirBoletaForm):
    """HU21 · RF29 · Mismo flujo que la boleta, más los datos de facturación (sin venta fiada)."""

    rut_facturacion = forms.CharField(label="RUT de facturación", max_length=12, validators=[validar_rut])
    razon_social = forms.CharField(label="Razón social", max_length=150)
    giro = forms.CharField(label="Giro", max_length=150)
    direccion_facturacion = forms.CharField(label="Dirección de facturación", max_length=200)

    def clean_rut_facturacion(self):
        return normalizar_rut(self.cleaned_data["rut_facturacion"])


class BoletaModificarForm(Formulario):
    """HU20 · RF27 · RNF23 · Observación y monto de cada línea (# DEMO: pendiente V02)."""

    observacion = forms.CharField(label="Observación", required=False, widget=forms.Textarea(attrs={"rows": 2}))
    version_leida = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, boleta, **kwargs):
        super().__init__(*args, **kwargs)
        self.boleta = boleta
        self.lineas = list(boleta.lineas.all())
        self.fields["observacion"].initial = boleta.observacion
        self.fields["version_leida"].initial = boleta.version
        for indice, linea in enumerate(self.lineas, start=1):
            self.fields[f"monto_{linea.pk}"] = forms.IntegerField(
                label=f"Monto línea {indice}: {linea.descripcion}", min_value=0, initial=linea.monto,
                error_messages={"min_value": "El monto no puede ser negativo."},
            )
            self.fields[f"monto_{linea.pk}"].widget.attrs["class"] = "input w-full"

    def clean(self):
        datos = super().clean()
        if datos.get("version_leida") is not None and datos["version_leida"] != self.boleta.version:
            raise forms.ValidationError(MENSAJE_CONFLICTO, code="conflicto_version")
        return datos

    def montos(self):
        return {l.pk: self.cleaned_data[f"monto_{l.pk}"] for l in self.lineas}


class AnularBoletaForm(Formulario):
    """HU20 · RF28 · Motivo obligatorio."""

    motivo = forms.CharField(label="Motivo de la anulación", widget=forms.Textarea(attrs={"rows": 3}),
                             error_messages={"required": "Indique el motivo de la anulación."})
