from django.contrib.auth import get_user_model
from django.db.models import Q

from core.forms import FormularioModelo
from core.validadores import normalizar_rut

from .models import Empleado


class EmpleadoForm(FormularioModelo):
    """HU14 · RF18"""

    class Meta:
        model = Empleado
        fields = ["rut", "nombres", "apellidos", "telefono", "usuario", "solicita_productos", "ejecuta_servicios", "activo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Usuario = get_user_model()
        libres = Usuario.objects.exclude(perfil=Usuario.CLIENTE).filter(
            Q(empleado__isnull=True) | Q(empleado=self.instance.pk or 0)
        )
        self.fields["usuario"].queryset = libres.order_by("username")
        self.fields["rut"].widget.attrs["placeholder"] = "12345678-9"
        if self.instance.pk:
            self.fields["rut"].disabled = True

    def clean_rut(self):
        return normalizar_rut(self.cleaned_data["rut"])
