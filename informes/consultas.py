"""HU22 · Informes · RF30 · RNF03 · CU15. Una sola función arma las filas de cada informe.

La misma salida la usan la vista previa, la impresión y (en S6) la exportación (HU23).
"""

from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal

from django.db.models import DecimalField, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from abastecimiento.models import LineaOrden, LineaRecepcion
from reservas.models import Reserva, ServicioRealizado
from ventas.models import Boleta, Factura

# RNF03: tiempo comprometido solo para informes de hasta 1 mes y 1.000 filas.
MAX_DIAS_PEQUENO = 31
MAX_FILAS_PEQUENO = 1000

TIPOS = {
    "servicios": {"titulo": "Servicios realizados", "filtros": ["cliente", "servicio", "empleado"], "icono": "tools",
                  "descripcion": "Qué se hizo, a quién y qué mecánico lo realizó."},
    "ventas": {"titulo": "Ventas", "filtros": ["cliente", "servicio", "empleado"], "icono": "cash-coin",
               "descripcion": "Boletas y facturas con totales, anuladas y ventas fiadas."},
    "reservas": {"titulo": "Reservas", "filtros": ["cliente", "servicio"], "icono": "calendar-check",
                 "descripcion": "Horas tomadas por Internet y en el local, y su resultado."},
    "abastecimiento": {"titulo": "Abastecimiento", "filtros": ["proveedor", "empleado"], "icono": "truck",
                       "descripcion": "Productos pedidos a proveedores, recibidos y pendientes."},
}


@dataclass
class Informe:
    tipo: str
    titulo: str
    desde: object
    hasta: object
    columnas: list  # [(nombre, formato)] formato: texto | fecha | fecha_hora | pesos | cantidad
    filas: list = field(default_factory=list)
    totales: list = field(default_factory=list)  # [(etiqueta, valor, formato)]
    filtros_aplicados: list = field(default_factory=list)  # [(etiqueta, valor)]

    @property
    def grande(self):
        """RNF03 · Más de 1 mes o más de 1.000 filas: sin tiempo comprometido."""
        return (self.hasta - self.desde).days + 1 > MAX_DIAS_PEQUENO or len(self.filas) > MAX_FILAS_PEQUENO


def rango_por_defecto():
    hoy = timezone.localdate()
    return hoy - timedelta(days=29), hoy


def rango_es_grande(desde, hasta):
    return (hasta - desde).days + 1 > MAX_DIAS_PEQUENO


def generar(tipo, desde, hasta, cliente=None, servicio=None, empleado=None, proveedor=None):
    informe = Informe(tipo=tipo, titulo=TIPOS[tipo]["titulo"], desde=desde, hasta=hasta, columnas=[])
    informe.filtros_aplicados = [("Desde", desde.strftime("%d-%m-%Y")), ("Hasta", hasta.strftime("%d-%m-%Y"))]
    for etiqueta, valor in (("Cliente", cliente), ("Servicio", servicio), ("Empleado", empleado), ("Proveedor", proveedor)):
        if valor is not None:
            informe.filtros_aplicados.append((etiqueta, str(valor)))
    _GENERADORES[tipo](informe, cliente=cliente, servicio=servicio, empleado=empleado, proveedor=proveedor)
    return informe


def _servicios(informe, cliente, servicio, empleado, **_):
    consulta = (ServicioRealizado.objects.filter(fecha__range=(informe.desde, informe.hasta))
                .select_related("cliente", "servicio", "empleado").order_by("fecha", "id"))
    if cliente:
        consulta = consulta.filter(cliente=cliente)
    if servicio:
        consulta = consulta.filter(servicio=servicio)
    if empleado:
        consulta = consulta.filter(empleado=empleado)
    informe.columnas = [("Fecha", "fecha"), ("Cliente", "texto"), ("Servicio", "texto"), ("Mecánico", "texto"),
                        ("Documento", "texto"), ("Precio de catálogo", "pesos")]
    informe.filas = [[s.fecha, s.cliente.nombre_completo, s.servicio.nombre, s.empleado.nombre_completo,
                      s.get_estado_documento_display(), s.servicio.precio] for s in consulta]
    informe.totales = [("Servicios realizados", len(informe.filas), "texto"),
                       ("Valor de catálogo", sum(f[5] for f in informe.filas), "pesos")]


def _ventas(informe, cliente, servicio, empleado, **_):
    boletas = Boleta.objects.filter(fecha_emision__date__range=(informe.desde, informe.hasta)).select_related("cliente")
    facturas = Factura.objects.filter(fecha__range=(informe.desde, informe.hasta)).select_related("cliente")
    if cliente:
        boletas, facturas = boletas.filter(cliente=cliente), facturas.filter(cliente=cliente)
    if servicio:
        boletas = boletas.filter(lineas__servicio_realizado__servicio=servicio).distinct()
        facturas = facturas.filter(lineas__servicio_realizado__servicio=servicio).distinct()
    if empleado:
        # El empleado de una venta es quien la emitió o registró.
        boletas = boletas.filter(emitida_por__empleado=empleado)
        facturas = facturas.filter(registrada_por__empleado=empleado)
    informe.columnas = [("Número", "texto"), ("Tipo", "texto"), ("Fecha", "fecha"), ("Cliente", "texto"),
                        ("Total", "pesos"), ("Estado", "texto"), ("Fiada", "texto")]
    filas = [[b.numero, "Boleta", timezone.localtime(b.fecha_emision).date(), b.cliente.nombre_completo, b.total,
              b.get_estado_display(), "Sí" if b.fiada else "No"] for b in boletas]
    filas += [[f.numero, "Factura", f.fecha, f.cliente.nombre_completo, f.total, "Registrada", "No"] for f in facturas]
    informe.filas = sorted(filas, key=lambda f: (f[2], f[1], f[0]))
    vigentes = [f for f in informe.filas if f[5] != "Anulada"]
    informe.totales = [("Documentos", len(informe.filas), "texto"),
                       ("Anulados", len(informe.filas) - len(vigentes), "texto"),
                       ("Total vendido (sin anuladas)", sum(f[4] for f in vigentes), "pesos"),
                       ("Total fiado (sin anuladas)", sum(f[4] for f in vigentes if f[6] == "Sí"), "pesos")]


def _reservas(informe, cliente, servicio, **_):
    consulta = (Reserva.objects.filter(fecha__range=(informe.desde, informe.hasta))
                .select_related("cliente", "servicio").order_by("fecha", "hora_inicio"))
    if cliente:
        consulta = consulta.filter(cliente=cliente)
    if servicio:
        consulta = consulta.filter(servicio=servicio)
    informe.columnas = [("Número", "texto"), ("Fecha", "fecha"), ("Hora", "texto"), ("Cliente", "texto"),
                        ("Servicio", "texto"), ("Canal", "texto"), ("Estado", "texto")]
    informe.filas = [[r.numero, r.fecha, r.hora_inicio.strftime("%H:%M"), r.cliente.nombre_completo, r.servicio.nombre,
                      r.get_canal_display(), r.get_estado_display()] for r in consulta]
    informe.totales = [("Reservas", len(informe.filas), "texto")] + [
        (etiqueta, sum(1 for f in informe.filas if f[6] == etiqueta), "texto") for _, etiqueta in Reserva.ESTADOS
    ] + [(f"Canal {etiqueta.lower()}", sum(1 for f in informe.filas if f[5] == etiqueta), "texto")
         for _, etiqueta in Reserva.CANALES]


def _abastecimiento(informe, proveedor, empleado, **_):
    recibido = (LineaRecepcion.objects.filter(recepcion__orden=OuterRef("orden"), producto=OuterRef("producto"))
                .values("producto").annotate(total=Sum("cantidad")).values("total"))
    consulta = (LineaOrden.objects.filter(orden__fecha__range=(informe.desde, informe.hasta))
                .select_related("orden__proveedor", "producto")
                .annotate(recibido=Coalesce(Subquery(recibido), Value(Decimal("0")),
                                            output_field=DecimalField(max_digits=10, decimal_places=2)))
                .order_by("orden__numero", "id"))
    if proveedor:
        consulta = consulta.filter(orden__proveedor=proveedor)
    if empleado:
        consulta = consulta.filter(orden__creada_por=empleado)
    informe.columnas = [("Orden", "texto"), ("Fecha", "fecha"), ("Proveedor", "texto"), ("Producto", "texto"),
                        ("Solicitado", "cantidad"), ("Recibido", "cantidad"), ("Pendiente", "cantidad")]
    informe.filas = [[l.orden.numero, l.orden.fecha, l.orden.proveedor.razon_social, l.producto.descripcion,
                      l.cantidad_solicitada, l.recibido, max(Decimal("0"), l.cantidad_solicitada - l.recibido)]
                     for l in consulta]
    informe.totales = [("Órdenes", len({f[0] for f in informe.filas}), "texto"),
                       ("Líneas", len(informe.filas), "texto"),
                       ("Líneas con pendiente", sum(1 for f in informe.filas if f[6] > 0), "texto")]


_GENERADORES = {"servicios": _servicios, "ventas": _ventas, "reservas": _reservas, "abastecimiento": _abastecimiento}


def formatear(valor, formato):
    """Texto para pantalla, impresión, .txt y .docx."""
    if valor is None:
        return ""
    if formato == "fecha":
        return valor.strftime("%d-%m-%Y")
    if formato == "pesos":
        return f"${int(valor):,}".replace(",", ".")
    if formato == "cantidad":
        texto = f"{valor:f}"
        return (texto.rstrip("0").rstrip(".") if "." in texto else texto).replace(".", ",")
    return str(valor)
