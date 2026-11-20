from django import forms

from abastecimiento.models import Proveedor
from catalogo.models import Servicio
from clientes.models import Cliente
from core.forms import CampoFecha, Formulario
from personal.models import Empleado

from .consultas import TIPOS, rango_por_defecto


class InformeForm(Formulario):
    """HU22 · RF30 · Filtros por fecha, cliente, servicio, empleado y proveedor (según el tipo)."""

    desde = CampoFecha(label="Desde", required=False)
    hasta = CampoFecha(label="Hasta", required=False)
    cliente = forms.ModelChoiceField(label="Cliente", queryset=Cliente.objects.all(), required=False, empty_label="Todos")
    servicio = forms.ModelChoiceField(label="Servicio", queryset=Servicio.objects.all(), required=False, empty_label="Todos")
    empleado = forms.ModelChoiceField(label="Empleado", queryset=Empleado.objects.all(), required=False, empty_label="Todos")
    proveedor = forms.ModelChoiceField(label="Proveedor", queryset=Proveedor.objects.all(), required=False, empty_label="Todos")

    def __init__(self, *args, tipo, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre in ("cliente", "servicio", "empleado", "proveedor"):
            if nombre not in TIPOS[tipo]["filtros"]:
                del self.fields[nombre]

    def clean(self):
        datos = super().clean()
        desde_def, hasta_def = rango_por_defecto()
        datos["desde"] = datos.get("desde") or desde_def
        datos["hasta"] = datos.get("hasta") or hasta_def
        if datos["desde"] > datos["hasta"]:
            self.add_error("hasta", "La fecha «hasta» debe ser igual o posterior a «desde».")
        return datos
