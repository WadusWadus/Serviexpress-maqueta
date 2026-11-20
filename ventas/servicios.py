"""Área 6 · Lógica de ventas (sin vistas). HU19, HU20, HU21 · CU12, CU13."""

from django.db import transaction
from django.utils import timezone

from clientes.models import MovimientoFiado
from core.auditoria import registrar
from core.correlativos import siguiente
from core.models import RegistroAuditoria
from reservas.models import ServicioRealizado

from .models import Boleta, Factura, LineaBoleta, LineaFactura

TASA_IVA = 0.19


class VentaNoPermitida(Exception):
    pass


def servicios_pendientes(cliente):
    """Servicios realizados del cliente que aún no tienen boleta ni factura."""
    return (ServicioRealizado.objects.filter(cliente=cliente, estado_documento=ServicioRealizado.PENDIENTE)
            .select_related("servicio", "empleado").order_by("fecha", "id"))


def _bloquear_pendientes(cliente, servicios):
    """Vuelve a leer los servicios dentro de la transacción y verifica que sigan pendientes."""
    ids = [s.pk for s in servicios]
    bloqueados = list(ServicioRealizado.objects.select_for_update().select_related("servicio")
                      .filter(pk__in=ids, cliente=cliente, estado_documento=ServicioRealizado.PENDIENTE)
                      .order_by("fecha", "id"))
    if not bloqueados or len(bloqueados) != len(ids):
        raise VentaNoPermitida("Alguno de los servicios ya fue documentado o no pertenece al cliente. Recargue la página.")
    return bloqueados


def _descripcion(realizado):
    return f"{realizado.servicio.nombre} ({realizado.fecha:%d-%m-%Y})"


MENSAJE_NO_HABILITADO = "El cliente no está habilitado para comprar fiado."


def _movimiento_fiado(boleta, monto, descripcion):
    """HU07 · RF08, RF09 · Cada cambio en una boleta fiada mueve el saldo del cliente."""
    if boleta.fiada and monto:
        MovimientoFiado.objects.create(cliente=boleta.cliente, boleta=boleta, monto=monto, descripcion=descripcion)


@transaction.atomic
def emitir_boleta(cliente, servicios, usuario, observacion="", fiada=False):
    """HU19 · RF26 · Número correlativo, líneas, total, servicios → DOCUMENTADO y log CREAR.

    HU07 · Flujo 3a de CU12: venta fiada solo para clientes habilitados (validado aquí, en el servidor).
    """
    if fiada and not cliente.fiado_habilitado:
        raise VentaNoPermitida(MENSAJE_NO_HABILITADO)
    realizados = _bloquear_pendientes(cliente, servicios)
    boleta = Boleta.objects.create(
        numero=siguiente("boleta"), cliente=cliente, total=sum(r.servicio.precio for r in realizados),
        emitida_por=usuario, observacion=observacion, fiada=fiada,
    )
    for r in realizados:
        LineaBoleta.objects.create(boleta=boleta, servicio_realizado=r, descripcion=_descripcion(r), monto=r.servicio.precio)
    ServicioRealizado.objects.filter(pk__in=[r.pk for r in realizados]).update(estado_documento=ServicioRealizado.DOCUMENTADO)
    _movimiento_fiado(boleta, boleta.total, f"Venta fiada · boleta N° {boleta.numero}")
    registrar(usuario, RegistroAuditoria.CREAR, "Boleta", boleta.numero, {
        "cliente": cliente.rut, "total": boleta.total, "fiada": fiada,
        "lineas": [{"descripcion": l.descripcion, "monto": l.monto} for l in boleta.lineas.all()],
    })
    return boleta


@transaction.atomic
def modificar_boleta(boleta, usuario, observacion, montos):
    """HU20 · RF27 · Guarda en el log el valor anterior y nuevo de cada campo cambiado.

    `montos`: {id_de_linea: monto_nuevo}. Qué campos son modificables no lo define el caso.
    # DEMO: pendiente V02
    """
    if boleta.anulada:
        raise VentaNoPermitida("Una boleta anulada no se puede modificar.")
    cambios = {}
    if (observacion or "") != boleta.observacion:
        cambios["observacion"] = {"anterior": boleta.observacion, "nuevo": observacion}
        boleta.observacion = observacion
    for indice, linea in enumerate(boleta.lineas.all(), start=1):
        nuevo = montos.get(linea.pk, linea.monto)
        if nuevo != linea.monto:
            cambios[f"línea {indice} monto"] = {"anterior": linea.monto, "nuevo": nuevo, "descripcion": linea.descripcion}
            linea.monto = nuevo
            linea.save(update_fields=["monto"])
    if not cambios:
        return boleta, {}
    total_anterior = boleta.total
    boleta.total = sum(boleta.lineas.values_list("monto", flat=True))
    if boleta.total != total_anterior:
        cambios["total"] = {"anterior": total_anterior, "nuevo": boleta.total}
        _movimiento_fiado(boleta, boleta.total - total_anterior, f"Ajuste por modificación de la boleta N° {boleta.numero}")
    boleta.save()
    registrar(usuario, RegistroAuditoria.MODIFICAR, "Boleta", boleta.numero, {"cambios": cambios})
    return boleta, cambios


@transaction.atomic
def anular_boleta(boleta, usuario, motivo):
    """HU20 · RF28 · Conserva líneas y montos; los servicios vuelven a PENDIENTE."""
    if boleta.anulada:
        raise VentaNoPermitida("La boleta ya está anulada.")
    if not (motivo or "").strip():
        raise VentaNoPermitida("Motivo: indique el motivo de la anulación.")
    boleta.estado = Boleta.ANULADA
    boleta.motivo_anulacion = motivo.strip()
    boleta.anulada_por = usuario
    boleta.anulada_en = timezone.now()
    boleta.save()
    ids = boleta.lineas.values_list("servicio_realizado_id", flat=True)
    ServicioRealizado.objects.filter(pk__in=list(ids)).update(estado_documento=ServicioRealizado.PENDIENTE)
    # El saldo no queda inflado: se reversa todo lo que la boleta sumó (total vigente al anular).
    _movimiento_fiado(boleta, -boleta.total, f"Reverso por anulación de la boleta N° {boleta.numero}")
    registrar(usuario, RegistroAuditoria.ANULAR, "Boleta", boleta.numero,
              {"motivo": boleta.motivo_anulacion, "total": boleta.total})
    return boleta


def desglose_iva(total):
    """El caso no dice si los precios incluyen IVA. # DEMO: pendiente V02 (se tratan como precio final)."""
    neto = round(total / (1 + TASA_IVA))
    return neto, total - neto


@transaction.atomic
def registrar_factura(cliente, servicios, usuario, datos):
    """HU21 · RF29 · Un servicio va en boleta o en factura, no en ambas."""
    realizados = _bloquear_pendientes(cliente, servicios)
    total = sum(r.servicio.precio for r in realizados)
    neto, iva = desglose_iva(total)
    factura = Factura.objects.create(
        numero=siguiente("factura"), cliente=cliente, neto=neto, iva=iva, total=total, registrada_por=usuario, **datos,
    )
    for r in realizados:
        LineaFactura.objects.create(factura=factura, servicio_realizado=r, descripcion=_descripcion(r), monto=r.servicio.precio)
    ServicioRealizado.objects.filter(pk__in=[r.pk for r in realizados]).update(estado_documento=ServicioRealizado.DOCUMENTADO)
    registrar(usuario, RegistroAuditoria.CREAR, "Factura", factura.numero, {
        "cliente": cliente.rut, "rut_facturacion": factura.rut_facturacion, "total": total,
    })
    return factura
