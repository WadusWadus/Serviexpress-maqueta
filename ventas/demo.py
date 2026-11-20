"""Datos demo · S3 · servicios realizados, boletas y factura (sección 10)."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from catalogo.models import Servicio
from clientes.models import Cliente
from personal.models import Empleado
from reservas.models import ServicioRealizado

from . import servicios as srv
from .models import Boleta


def _realizado(cliente, nombre_servicio, dias_atras, mecanico, observacion=""):
    return ServicioRealizado.objects.create(
        cliente=cliente, servicio=Servicio.objects.get(nombre=nombre_servicio), empleado=mecanico,
        fecha=timezone.localdate() - timedelta(days=dias_atras), observacion=observacion,
    )


def cargar(salida):
    if not Boleta.objects.exists():
        _cargar_s3(salida)
    if not Boleta.objects.filter(fiada=True).exists():
        _cargar_fiado(salida)


def _cargar_fiado(salida):
    """S5 · 2 boletas fiadas de cliente1, para que su saldo se vea (HU07)."""
    administrativo = get_user_model().objects.get(username="administrativo")
    mecanico = Empleado.objects.get(usuario__username="mecanico")
    cliente1 = Cliente.objects.get(usuario__username="cliente1")
    for nombre, dias in (("Cambio de pastillas", 9), ("Revisión de frenos", 8)):
        realizado = _realizado(cliente1, nombre, dias, mecanico)
        srv.emitir_boleta(cliente1, [realizado], administrativo, "Venta fiada de demostración.", fiada=True)
    salida.write(f"  ventas: 2 boletas fiadas de cliente1 (saldo {cliente1.saldo_fiado:,})".replace(",", "."))


def _cargar_s3(salida):
    usuarios = get_user_model().objects
    administrativo = usuarios.get(username="administrativo")
    mecanico = Empleado.objects.get(usuario__username="mecanico")
    cliente1 = Cliente.objects.get(usuario__username="cliente1")
    cliente3 = Cliente.objects.get(usuario__username="cliente3")

    # cliente1: 2 pendientes, 1 con boleta emitida y 1 con boleta anulada (su servicio vuelve a quedar pendiente).
    _realizado(cliente1, "Revisión de frenos", 2, mecanico)
    _realizado(cliente1, "Cambio de batería", 1, mecanico, "Batería con 3 años de uso.")
    emitida = _realizado(cliente1, "Cambio de aceite", 6, mecanico)
    srv.emitir_boleta(cliente1, [emitida], administrativo, "Pago en efectivo.")
    anulada = _realizado(cliente1, "Mantención básica", 5, mecanico)
    boleta = srv.emitir_boleta(cliente1, [anulada], administrativo)
    srv.anular_boleta(boleta, administrativo, "Error en el servicio: se boleteó un servicio distinto.")

    # Otro cliente con factura.
    facturado = _realizado(cliente3, "Cambio de pastillas", 3, mecanico)
    srv.registrar_factura(cliente3, [facturado], administrativo, {
        "rut_facturacion": "76123456-0", "razon_social": "Transportes Fernández SpA", "giro": "Transporte de carga",
        "direccion_facturacion": "Camino a Melipilla 900, Maipú",
    })
    salida.write("  ventas: 4 servicios de cliente1 (1 boleta emitida, 1 anulada), 1 factura")
