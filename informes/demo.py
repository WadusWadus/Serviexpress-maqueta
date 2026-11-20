"""Datos demo · S5 · historial de los últimos 60 días para que los informes muestren datos.

Las órdenes de pedido no se agregan aquí: las de S4 y S5 ya están dentro de los 60 días y así
la demo de HU17 conserva su numeración (eliminar la N° 5 y la nueva recibe la N° 6).
"""

from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from catalogo.models import Servicio
from clientes.models import Cliente
from personal.models import Empleado
from reservas.models import Reserva, ServicioRealizado
from ventas import servicios as srv_ventas
from ventas.models import Boleta


def _es_dia_habil_pasado(fecha):
    """Mismo criterio que la agenda (horario y festivos), pero hacia atrás."""
    from django.conf import settings

    from reservas.servicios import es_festivo
    return fecha.weekday() in settings.SERVIEXPRESS["DIAS_ATENCION"] and not es_festivo(fecha)


def cargar(salida):
    cargar_historial(salida)
    cargar_visitas(salida)


def cargar_historial(salida):
    hoy = timezone.localdate()
    if Reserva.objects.filter(fecha__lt=hoy - timedelta(days=15)).exists():
        return
    usuarios = get_user_model().objects
    administrativo = usuarios.get(username="administrativo")
    mecanicos = list(Empleado.objects.filter(ejecuta_servicios=True, usuario__perfil="MECANICO")) or \
        list(Empleado.objects.filter(ejecuta_servicios=True))
    clientes = list(Cliente.objects.order_by("pk"))
    servicios = list(Servicio.objects.reservables().order_by("pk"))
    reservas = boletas = 0
    for dias in range(60, 10, -1):  # los últimos 10 días ya tienen datos de S2–S5
        fecha = hoy - timedelta(days=dias)
        if not _es_dia_habil_pasado(fecha):
            continue
        for i in range(dias % 3 + 1):
            cliente = clientes[(dias + i) % len(clientes)]
            servicio = servicios[(dias * 3 + i) % len(servicios)]
            anulada = (dias + i) % 7 == 0
            reserva = Reserva.objects.create(
                cliente=cliente, servicio=servicio, fecha=fecha, hora_inicio=time(9 + 2 * i),
                estado=Reserva.ANULADA if anulada else Reserva.ATENDIDA,
                canal=Reserva.WEB if (dias + i) % 3 else Reserva.LOCAL, creada_por=cliente.usuario,
            )
            reservas += 1
            if anulada:
                continue
            realizado = ServicioRealizado.objects.create(
                cliente=cliente, servicio=servicio, reserva=reserva, fecha=fecha,
                empleado=mecanicos[(dias + i) % len(mecanicos)],
            )
            if (dias + i) % 4:
                boleta = srv_ventas.emitir_boleta(cliente, [realizado], administrativo)
                Boleta.objects.filter(pk=boleta.pk).update(
                    fecha_emision=timezone.make_aware(datetime.combine(fecha, time(18))))
                boletas += 1
    salida.write(f"  informes: historial de 60 días ({reservas} reservas, {boletas} boletas)")



def cargar_visitas(salida):
    """S6 · Visitas de los últimos 90 días, con más visitas los lunes para que el gráfico varíe."""
    import random

    from .models import VisitaWeb

    if VisitaWeb.objects.exists():
        return
    azar = random.Random(2026)  # siempre los mismos datos
    rutas = ["/", "/", "/cuentas/ingresar/", "/reservas/nueva/", "/reservas/nueva/fecha/", "/reservas/mis-reservas/"]
    hoy = timezone.localdate()
    visitas = []
    for dias in range(90, 0, -1):
        fecha = hoy - timedelta(days=dias)
        cantidad = 12 + (dias % 5) * 2 + (18 if fecha.weekday() == 0 else 0) + azar.randint(0, 6)
        for n in range(cantidad):
            momento = timezone.make_aware(datetime.combine(fecha, time(8 + n % 12, azar.randint(0, 59))))
            visitas.append(VisitaWeb(fecha_hora=momento, ruta=azar.choice(rutas), clave_sesion=f"demo-{dias}-{n}"))
    VisitaWeb.objects.bulk_create(visitas)
    salida.write(f"  informes: {len(visitas)} visitas web de los últimos 90 días")
