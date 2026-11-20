"""Área 5 · Lógica de abastecimiento (sin vistas). HU16, HU17, HU18."""

from decimal import Decimal

from django.db import transaction

from core.auditoria import registrar
from core.correlativos import siguiente
from core.models import RegistroAuditoria

from .models import LineaOrden, LineaRecepcion, OrdenPedido, Recepcion


class ProductoNoSolicitado(Exception):
    """HU18 · RF25 · Flujo 4a de CU11."""


class RecepcionInvalida(Exception):
    pass


def _contenido(lineas):
    return [{"producto": l.producto.codigo, "cantidad": l.cantidad_solicitada} for l in lineas]


@transaction.atomic
def crear_orden(empleado, usuario, proveedor, lineas, observacion=""):
    """HU16 · RF20 · El número se asigna al confirmar, con el correlativo (no reutiliza números)."""
    orden = OrdenPedido.objects.create(numero=siguiente("orden_pedido"), proveedor=proveedor, creada_por=empleado,
                                       observacion=observacion)
    creadas = [LineaOrden.objects.create(orden=orden, producto=p, cantidad_solicitada=c) for p, c in lineas]
    registrar(usuario, RegistroAuditoria.CREAR, "OrdenPedido", orden.numero, {
        "proveedor": proveedor.razon_social, "creada_por": empleado.nombre_completo, "lineas": _contenido(creadas),
    })
    return orden


def advertencias_recepcion(orden, cantidades):
    """HU18 · Flujo 4b: una advertencia por cada producto cuya cantidad recibida difiere de la pendiente."""
    avisos = []
    for linea in orden.lineas.select_related("producto"):
        recibida = cantidades.get(linea.producto_id, Decimal("0"))
        pendiente = linea.cantidad_pendiente
        if recibida != pendiente:
            avisos.append(
                f"La cantidad recibida de {linea.producto.descripcion} ({_fmt(recibida)}) difiere de la pendiente "
                f"({_fmt(pendiente)}). ¿Confirma la recepción?"
            )
    return avisos


def _fmt(numero):
    texto = f"{numero:f}"
    return (texto.rstrip("0").rstrip(".") if "." in texto else texto).replace(".", ",")


def sumar_extras(orden, cantidades, extras):
    """Agrega los productos ingresados por código. RF25: si no están en la orden, se rechaza todo."""
    total = dict(cantidades)
    por_codigo = {l.producto.codigo: l.producto_id for l in orden.lineas.select_related("producto")}
    for codigo, cantidad in extras:
        codigo = (codigo or "").strip().upper()
        if not codigo:
            continue
        if codigo not in por_codigo:
            raise ProductoNoSolicitado(f"Producto no solicitado en la orden N° {orden.numero}")
        total[por_codigo[codigo]] = total.get(por_codigo[codigo], Decimal("0")) + (cantidad or Decimal("0"))
    return total


@transaction.atomic
def registrar_recepcion(orden, usuario, cantidades, extras=(), confirmar_diferencias=False, observacion=""):
    """HU18 · RF24, RF25 · CU11.

    Devuelve (recepcion, advertencias). Si hay diferencias y no se confirmaron, no guarda nada
    y devuelve (None, advertencias). Un producto no solicitado lanza ProductoNoSolicitado.
    """
    total = sumar_extras(orden, cantidades, extras)
    if any(c < 0 for c in total.values()):
        raise RecepcionInvalida("Las cantidades recibidas no pueden ser negativas.")
    if not any(c > 0 for c in total.values()):
        raise RecepcionInvalida("Ingrese al menos una cantidad recibida.")
    avisos = advertencias_recepcion(orden, total)
    if avisos and not confirmar_diferencias:
        return None, avisos
    recepcion = Recepcion.objects.create(orden=orden, recibida_por=usuario, observacion=observacion)
    for producto_id, cantidad in total.items():
        if cantidad > 0:
            LineaRecepcion.objects.create(recepcion=recepcion, producto_id=producto_id, cantidad=cantidad)
    registrar(usuario, RegistroAuditoria.CREAR, "Recepcion", recepcion.pk, {
        "orden": orden.numero, "con_diferencias": bool(avisos),
        "lineas": [{"producto": l.producto.codigo, "cantidad": l.cantidad} for l in recepcion.lineas.select_related("producto")],
    })
    return recepcion, avisos


class OrdenConRecepciones(Exception):
    """HU17 · RF21 · Una orden con recepciones no se modifica ni se elimina."""


MENSAJE_CON_RECEPCIONES = "No se puede modificar ni eliminar una orden con recepciones registradas."


@transaction.atomic
def modificar_orden(orden, usuario, lineas, observacion=""):
    """HU17 · RF21 · RNF08 · Cambia productos y cantidades; el log guarda los valores anteriores."""
    orden = OrdenPedido.objects.select_for_update().get(pk=orden.pk)
    if orden.tiene_recepciones:
        raise OrdenConRecepciones(MENSAJE_CON_RECEPCIONES)
    anterior = {"lineas": _contenido(orden.lineas.select_related("producto")), "observacion": orden.observacion}
    orden.lineas.all().delete()
    nuevas = [LineaOrden.objects.create(orden=orden, producto=p, cantidad_solicitada=c) for p, c in lineas]
    orden.observacion = observacion
    orden.save()
    registrar(usuario, RegistroAuditoria.MODIFICAR, "OrdenPedido", orden.numero, {
        "anterior": anterior, "nuevo": {"lineas": _contenido(nuevas), "observacion": observacion},
    })
    return orden


@transaction.atomic
def eliminar_orden(orden, usuario):
    """HU17 · RF22 · Borra la orden y sus líneas. El correlativo no retrocede: el número no se reutiliza."""
    orden = OrdenPedido.objects.select_for_update().get(pk=orden.pk)
    if orden.tiene_recepciones:
        raise OrdenConRecepciones(MENSAJE_CON_RECEPCIONES)
    contenido = {"proveedor": orden.proveedor.razon_social, "fecha": orden.fecha,
                 "lineas": _contenido(orden.lineas.select_related("producto")), "observacion": orden.observacion}
    numero = orden.numero
    orden.delete()
    registrar(usuario, RegistroAuditoria.ELIMINAR, "OrdenPedido", numero, contenido)
    return numero
