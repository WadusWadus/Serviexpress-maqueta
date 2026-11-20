"""Panel de inicio: indicadores y listas según el perfil.

Vive en informes (la app que puede leer de todas) y core lo carga sin importarlo directamente.
"""

from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from abastecimiento.models import OrdenPedido
from clientes.models import Cliente, MovimientoFiado
from personal.servicios import empleado_de
from reservas.models import Reserva, ServicioRealizado
from ventas.models import Boleta, Factura


def _ventas_por_dia(dias=14):
    hoy = timezone.localdate()
    desde = hoy - timedelta(days=dias - 1)
    totales = {desde + timedelta(days=i): 0 for i in range(dias)}
    for fecha, total in Boleta.objects.filter(estado=Boleta.EMITIDA, fecha_emision__date__gte=desde).values_list("fecha_emision", "total"):
        totales[timezone.localtime(fecha).date()] = totales.get(timezone.localtime(fecha).date(), 0) + total
    for fecha, total in Factura.objects.filter(fecha__gte=desde).values_list("fecha", "total"):
        totales[fecha] = totales.get(fecha, 0) + total
    return {"etiquetas": [f"{d:%d-%m}" for d in totales], "valores": list(totales.values())}


def _personal(usuario):
    hoy = timezone.localdate()
    inicio_mes = hoy.replace(day=1)
    reservas_hoy = Reserva.objects.filter(fecha=hoy).exclude(estado=Reserva.ANULADA).select_related("cliente", "servicio")
    ventas_mes = (Boleta.objects.filter(estado=Boleta.EMITIDA, fecha_emision__date__gte=inicio_mes).aggregate(t=Sum("total"))["t"] or 0) + \
                 (Factura.objects.filter(fecha__gte=inicio_mes).aggregate(t=Sum("total"))["t"] or 0)
    ordenes = OrdenPedido.objects.prefetch_related("lineas", "recepciones")
    ordenes_abiertas = sum(1 for o in ordenes if o.estado != OrdenPedido.COMPLETA)
    return {
        "indicadores": [
            {"icono": "calendar2-week", "valor": reservas_hoy.filter(estado=Reserva.VIGENTE).count(), "nombre": "Reservas de hoy", "url": "agenda:lista"},
            {"icono": "clipboard-check", "valor": ServicioRealizado.objects.filter(estado_documento=ServicioRealizado.PENDIENTE).count(),
             "nombre": "Servicios por cobrar", "url": "ventas:boleta_nueva"},
            {"icono": "cash-coin", "valor": ventas_mes, "formato": "pesos", "nombre": "Ventas del mes", "url": "informes:inicio"},
            {"icono": "wallet2", "valor": MovimientoFiado.objects.aggregate(t=Sum("monto"))["t"] or 0, "formato": "pesos",
             "nombre": "Fiado por cobrar", "url": "clientes:fiado"},
            {"icono": "box-seam", "valor": ordenes_abiertas, "nombre": "Pedidos por recibir", "url": "abastecimiento:ordenes"},
        ],
        "agenda": reservas_hoy.order_by("hora_inicio"),
        "ultimas_boletas": Boleta.objects.select_related("cliente")[:6],
        "grafico": _ventas_por_dia(),
    }


def _mecanico(usuario):
    hoy = timezone.localdate()
    empleado = empleado_de(usuario)
    mios = ServicioRealizado.objects.filter(fecha=hoy, empleado=empleado) if empleado else ServicioRealizado.objects.none()
    reservas = Reserva.objects.filter(fecha=hoy, estado=Reserva.VIGENTE).select_related("cliente", "servicio").order_by("hora_inicio")
    return {
        "indicadores": [
            {"icono": "calendar2-week", "valor": reservas.count(), "nombre": "Reservas por atender hoy", "url": "atencion:inicio"},
            {"icono": "check2-circle", "valor": mios.count(), "nombre": "Servicios que registró hoy", "url": "atencion:realizados"},
        ],
        "agenda": reservas,
        "realizados": mios.select_related("cliente", "servicio")[:6],
    }


def _cliente(usuario):
    cliente = Cliente.objects.filter(usuario=usuario).first()
    if cliente is None:
        return {}
    ahora = timezone.localtime()
    proximas = [r for r in cliente.reservas.filter(estado=Reserva.VIGENTE, fecha__gte=ahora.date())
                .select_related("servicio").order_by("fecha", "hora_inicio") if r.modificable]
    return {
        "cliente": cliente,
        "proxima": proximas[0] if proximas else None,
        "otras": proximas[1:4],
        "atenciones": cliente.servicios_realizados.select_related("servicio", "empleado")[:5],
    }



def contexto(usuario):
    perfil = getattr(usuario, "perfil", None)
    if perfil in ("ADMIN", "ADMINISTRATIVO"):
        return {"tipo_panel": "personal", **_personal(usuario)}
    if perfil == "MECANICO":
        return {"tipo_panel": "mecanico", **_mecanico(usuario)}
    if perfil == "CLIENTE":
        return {"tipo_panel": "cliente", **_cliente(usuario)}
    return {"tipo_panel": "vacio"}
