"""RF18 · Restricciones por función del empleado (MAQUETA-SPEC 5.2). Valen también para ADMIN."""

from .models import Empleado


def empleado_de(usuario):
    """Empleado activo asociado a la cuenta, o None."""
    if not usuario.is_authenticated:
        return None
    return Empleado.objects.filter(usuario=usuario, activo=True).first()


def puede_solicitar_productos(usuario):
    empleado = empleado_de(usuario)
    return empleado is not None and empleado.solicita_productos


def puede_ejecutar_servicios(usuario):
    empleado = empleado_de(usuario)
    return empleado is not None and empleado.ejecuta_servicios
