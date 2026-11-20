"""RF20, RF22 · Correlativos (MAQUETA-SPEC 5.5).

No se usa max(numero) + 1: si se eliminara el último documento, su número se reutilizaría.
"""

from django.db import transaction

from .models import Correlativo


def siguiente(nombre):
    """Suma 1 al correlativo `nombre` y devuelve el número nuevo."""
    with transaction.atomic():
        Correlativo.objects.get_or_create(nombre=nombre)
        correlativo = Correlativo.objects.select_for_update().get(nombre=nombre)
        correlativo.ultimo += 1
        correlativo.save(update_fields=["ultimo"])
        return correlativo.ultimo
