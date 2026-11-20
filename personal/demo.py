"""Datos demo · S1 · empleados con sus funciones (sección 6)."""

from django.contrib.auth import get_user_model

from core.validadores import rut_con_dv

from .models import Empleado

# (usuario, rut, nombres, apellidos, solicita_productos, ejecuta_servicios)
EMPLEADOS_DEMO = [
    ("admin", 9876543, "Juan Pedro", "Administrador", True, True),
    ("administrativo", 15111222, "Ana", "Rojas", True, False),
    ("administrativo2", 16222333, "Bruno", "Díaz", False, True),
    ("mecanico", 17333444, "Carlos", "Muñoz", False, True),
    (None, 18444555, "Diego", "Paredes", False, True),
]


def cargar(salida):
    Usuario = get_user_model()
    for username, rut, nombres, apellidos, solicita, ejecuta in EMPLEADOS_DEMO:
        Empleado.objects.update_or_create(
            rut=rut_con_dv(rut),
            defaults={
                "nombres": nombres, "apellidos": apellidos, "telefono": "+56 9 5555 0000",
                "usuario": Usuario.objects.filter(username=username).first() if username else None,
                "solicita_productos": solicita, "ejecuta_servicios": ejecuta, "activo": True,
            },
        )
    salida.write("  personal: 5 empleados")
