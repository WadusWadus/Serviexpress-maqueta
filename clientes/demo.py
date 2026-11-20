"""Datos demo · S1 · fichas de cliente1, cliente2 y 3 clientes más."""

from django.contrib.auth import get_user_model

from core.validadores import rut_con_dv
from cuentas.demo import CONTRASENA_DEMO

from .models import Cliente

# (usuario, rut, nombres, apellidos, teléfono, dirección)
CLIENTES_DEMO = [
    ("cliente1", 12345678, "María", "González", "+56 9 8765 4321", "Av. Pajaritos 1234, Maipú"),
    ("cliente2", 13456789, "Pedro", "Soto", "+56 9 7654 3210", "Los Aromos 55, Maipú"),
    ("cliente3", 14567890, "Lucía", "Fernández", "+56 9 6543 2109", "Camino a Melipilla 900, Maipú"),
    ("cliente4", 10987654, "Jorge", "Ramírez", "+56 9 5432 1098", "5 de Abril 300, Maipú"),
    ("cliente5", 11222333, "Camila", "Torres", "+56 9 4321 0987", "Américo Vespucio 2500, Cerrillos"),
]


def cargar(salida):
    Usuario = get_user_model()
    for username, rut, nombres, apellidos, telefono, direccion in CLIENTES_DEMO:
        cuenta, creada = Usuario.objects.get_or_create(
            username=username,
            defaults={"perfil": Usuario.CLIENTE, "first_name": nombres, "last_name": apellidos,
                      "email": f"{username}@correo.demo"},
        )
        if creada:
            cuenta.set_password(CONTRASENA_DEMO)
            cuenta.save()
        Cliente.objects.update_or_create(
            usuario=cuenta,
            defaults={"rut": rut_con_dv(rut), "nombres": nombres, "apellidos": apellidos, "telefono": telefono,
                      "email": cuenta.email, "direccion": direccion},
        )
    salida.write("  clientes: 5 fichas")
    # S5 · cliente1 habilitado para fiado; cliente2 no (HU06).
    Cliente.objects.filter(usuario__username="cliente1").update(fiado_habilitado=True)
    Cliente.objects.filter(usuario__username="cliente2").update(fiado_habilitado=False)
