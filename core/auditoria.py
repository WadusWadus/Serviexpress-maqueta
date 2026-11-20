"""RNF06, RNF08 · Única forma de escribir en el log de auditoría (MAQUETA-SPEC 5.3)."""

from django.core.serializers.json import DjangoJSONEncoder
import json

from .models import RegistroAuditoria


def registrar(usuario, operacion, entidad, entidad_id, detalle=None):
    """Guarda una línea en el log. `usuario` puede ser None o un usuario anónimo."""
    if usuario is not None and not getattr(usuario, "is_authenticated", False):
        usuario = None
    if detalle is not None:
        # Normaliza fechas, decimales, etc. para que el JSON sea siempre serializable.
        detalle = json.loads(json.dumps(detalle, cls=DjangoJSONEncoder))
    return RegistroAuditoria.objects.create(
        usuario=usuario,
        operacion=operacion,
        entidad=entidad,
        entidad_id=str(entidad_id) if entidad_id is not None else "",
        detalle=detalle,
    )


def historial(entidad, entidad_id):
    """Registros del log de una entidad, del más antiguo al más reciente."""
    return RegistroAuditoria.objects.filter(entidad=entidad, entidad_id=str(entidad_id)).order_by("fecha_hora", "id")
