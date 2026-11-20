from core.forms import CampoFecha, FormularioModelo

from .models import DiaFestivo


class DiaFestivoForm(FormularioModelo):
    """HU09 · RF12"""

    fecha = CampoFecha(label="Fecha")

    class Meta:
        model = DiaFestivo
        fields = ["fecha", "descripcion"]
