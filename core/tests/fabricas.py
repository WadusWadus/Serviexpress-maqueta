"""Fábricas para los tests. Crean objetos mínimos sin pasar por las pantallas.

Las contraseñas solo se fijan cuando el test las necesita (el hash PBKDF2 es lento a propósito, RNF05).
"""

import itertools

from django.apps import apps
from django.contrib.auth import get_user_model

from core.validadores import rut_con_dv

_ruts = itertools.count(20_000_000)
_codigos = itertools.count(1)


def nuevo_rut():
    return rut_con_dv(next(_ruts))


def crear_usuario(username, perfil="ADMIN", password=None, **extra):
    Usuario = get_user_model()
    usuario = Usuario(username=username, perfil=perfil, **extra)
    if password:
        usuario.set_password(password)
    else:
        usuario.set_unusable_password()
    usuario.save()
    return usuario


def crear_empleado(usuario=None, solicita_productos=False, ejecuta_servicios=True, **extra):
    Empleado = apps.get_model("personal", "Empleado")
    datos = {"rut": nuevo_rut(), "nombres": "Empleado", "apellidos": "Prueba"} | extra
    return Empleado.objects.create(usuario=usuario, solicita_productos=solicita_productos,
                                   ejecuta_servicios=ejecuta_servicios, **datos)


def crear_cliente(username=None, password=None, **extra):
    Cliente = apps.get_model("clientes", "Cliente")
    username = username or f"cli{next(_codigos)}"
    cuenta = crear_usuario(username, "CLIENTE", password)
    datos = {"rut": nuevo_rut(), "nombres": username.capitalize(), "apellidos": "Cliente"} | extra
    return Cliente.objects.create(usuario=cuenta, **datos)


def crear_producto(codigo=None, **extra):
    Producto = apps.get_model("catalogo", "Producto")
    datos = {"codigo": codigo or f"P{next(_codigos):04d}", "descripcion": "Producto de prueba"} | extra
    return Producto.objects.create(**datos)


def crear_servicio(nombre=None, precio=10000, **extra):
    Servicio = apps.get_model("catalogo", "Servicio")
    return Servicio.objects.create(nombre=nombre or f"Servicio {next(_codigos)}", precio=precio, **extra)


def proximo_dia_habil(desde=1):
    """Primer día con horas libres a partir de hoy + `desde` días (respeta festivos y horario)."""
    from datetime import timedelta

    from django.utils import timezone

    from reservas.servicios import horas_disponibles

    hoy = timezone.localdate()
    for dias in range(desde, desde + 15):
        fecha = hoy + timedelta(days=dias)
        if horas_disponibles(fecha):
            return fecha
    raise AssertionError("No hay días hábiles en las próximas dos semanas")


def crear_reserva(cliente, servicio=None, fecha=None, hora=None, **extra):
    from datetime import time

    Reserva = apps.get_model("reservas", "Reserva")
    datos = {"canal": "WEB", "creada_por": cliente.usuario} | extra
    return Reserva.objects.create(cliente=cliente, servicio=servicio or crear_servicio(),
                                  fecha=fecha or proximo_dia_habil(), hora_inicio=hora or time(10), **datos)


def crear_realizado(cliente, servicio=None, empleado=None, **extra):
    ServicioRealizado = apps.get_model("reservas", "ServicioRealizado")
    empleado = empleado or crear_empleado(crear_usuario(f"mec{next(_codigos)}", "MECANICO"))
    return ServicioRealizado.objects.create(cliente=cliente, servicio=servicio or crear_servicio(), empleado=empleado, **extra)


def crear_proveedor(razon_social="Lubricantes del Sur", **extra):
    Proveedor = apps.get_model("abastecimiento", "Proveedor")
    return Proveedor.objects.create(rut=nuevo_rut(), razon_social=razon_social, rubro=extra.pop("rubro", "Lubricantes"), **extra)
