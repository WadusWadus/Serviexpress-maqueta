"""Datos demo · S4 · 3 proveedores y 3 órdenes de `administrativo` (sección 10)."""

from decimal import Decimal

from django.contrib.auth import get_user_model

from catalogo.models import Producto
from core.validadores import rut_con_dv
from personal.models import Empleado

from . import servicios as srv
from .models import OrdenPedido, Proveedor

PROVEEDORES = [
    (76111222, "Lubricantes del Sur Ltda.", "Rosa Vera", "+56 2 2555 1000", "ventas@lubrisur.demo", "Lubricantes"),
    (76222333, "Frenos Chile SpA", "Marco Lagos", "+56 2 2555 2000", "contacto@frenoschile.demo", "Frenos"),
    (76333444, "Baterías y Eléctrico Maipú", "Inés Bravo", "+56 2 2555 3000", "pedidos@bateriasmaipu.demo",
     "Baterías y eléctrico"),
]


def _p(codigo):
    return Producto.objects.get(codigo=codigo)


def cargar(salida):
    for rut, razon, contacto, telefono, email, rubro in PROVEEDORES:
        Proveedor.objects.update_or_create(rut=rut_con_dv(rut), defaults={
            "razon_social": razon, "nombre_contacto": contacto, "telefono": telefono, "email": email,
            "rubro": rubro, "activo": True})
    salida.write("  abastecimiento: 3 proveedores")
    if OrdenPedido.objects.exists():
        return
    usuario = get_user_model().objects.get(username="administrativo")
    empleado = Empleado.objects.get(usuario=usuario)
    lubricantes, frenos, baterias = (Proveedor.objects.get(rut=rut_con_dv(p[0])) for p in PROVEEDORES)
    D = Decimal

    # Una sin recepción.
    srv.crear_orden(empleado, usuario, baterias, [(_p("BATERIA"), D("2")), (_p("AMPOLL"), D("10"))])
    # Una con recepción parcial.
    parcial = srv.crear_orden(empleado, usuario, frenos, [(_p("PAS-FRE"), D("6")), (_p("LIQ-FRE"), D("4"))])
    srv.registrar_recepcion(parcial, usuario, {_p("PAS-FRE").pk: D("4"), _p("LIQ-FRE").pk: D("4")},
                            confirmar_diferencias=True, observacion="Faltaron 2 juegos de pastillas.")
    # Una recepcionada completa.
    completa = srv.crear_orden(empleado, usuario, lubricantes, [(_p("ACE-10W40"), D("20")), (_p("FIL-ACE"), D("5"))])
    srv.registrar_recepcion(completa, usuario, {_p("ACE-10W40").pk: D("20"), _p("FIL-ACE").pk: D("5")})
    salida.write("  abastecimiento: 3 órdenes (sin recepción, parcial y completa)")
    _cargar_s5(salida)


def _cargar_s5(salida):
    """S5 · Órdenes sin recepciones para mostrar HU17 (modificar una y eliminar la última)."""
    usuario = get_user_model().objects.get(username="administrativo")
    empleado = Empleado.objects.get(usuario=usuario)
    lubricantes = Proveedor.objects.get(rut=rut_con_dv(PROVEEDORES[0][0]))
    D = Decimal
    srv.crear_orden(empleado, usuario, lubricantes, [(_p("ACE-10W40"), D("12")), (_p("FIL-AIR"), D("4"))],
                    "Para modificar en la demo de HU17.")
    srv.crear_orden(empleado, usuario, lubricantes, [(_p("REFRIG"), D("6"))], "Para eliminar en la demo de HU17.")
    salida.write("  abastecimiento: 2 órdenes sin recepciones (N° 4 y N° 5) para HU17")
