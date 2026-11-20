"""Área 6 · Ventas. HU19, HU20 (boletas) y HU21 (facturas) · CU12, CU13."""

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import ConVersion


class EliminacionNoPermitida(Exception):
    """RNF09 · Las boletas no se eliminan: se anulan."""


class BoletaQuerySet(models.QuerySet):
    def delete(self):
        raise EliminacionNoPermitida("Las boletas no se pueden eliminar; solo anular (RNF09).")


class Boleta(ConVersion):
    """HU19, HU20 · RF26, RF27, RF28 · RNF08, RNF09 · CU12.

    Documento interno: no tiene validez tributaria en la maqueta (V02).
    """

    EMITIDA = "EMITIDA"
    ANULADA = "ANULADA"
    ESTADOS = [(EMITIDA, "Emitida"), (ANULADA, "Anulada")]

    numero = models.PositiveIntegerField("N° de boleta", unique=True)
    cliente = models.ForeignKey("clientes.Cliente", verbose_name="cliente", on_delete=models.PROTECT, related_name="boletas")
    fecha_emision = models.DateTimeField("fecha de emisión", default=timezone.now)
    total = models.PositiveIntegerField("total")
    estado = models.CharField("estado", max_length=10, choices=ESTADOS, default=EMITIDA)
    motivo_anulacion = models.TextField("motivo de anulación", blank=True)
    anulada_por = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="anulada por", null=True, blank=True,
                                    on_delete=models.PROTECT, related_name="boletas_anuladas")
    anulada_en = models.DateTimeField("anulada el", null=True, blank=True)
    emitida_por = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="emitida por", on_delete=models.PROTECT,
                                    related_name="boletas_emitidas")
    observacion = models.TextField("observación", blank=True)
    fiada = models.BooleanField("venta fiada", default=False)  # HU07 · RF08 (S5)

    objects = BoletaQuerySet.as_manager()

    class Meta:
        verbose_name = "boleta"
        verbose_name_plural = "boletas"
        ordering = ["-numero"]

    def __str__(self):
        return f"Boleta N° {self.numero}"

    def delete(self, *args, **kwargs):
        raise EliminacionNoPermitida("Las boletas no se pueden eliminar; solo anular (RNF09).")

    @property
    def anulada(self):
        return self.estado == self.ANULADA


class LineaBoleta(models.Model):
    boleta = models.ForeignKey(Boleta, on_delete=models.PROTECT, related_name="lineas")
    servicio_realizado = models.ForeignKey("reservas.ServicioRealizado", on_delete=models.PROTECT, related_name="lineas_boleta")
    descripcion = models.CharField("descripción", max_length=200)
    monto = models.PositiveIntegerField("monto")

    class Meta:
        verbose_name = "línea de boleta"
        verbose_name_plural = "líneas de boleta"
        ordering = ["id"]

    def __str__(self):
        return f"{self.descripcion}: {self.monto}"


class Factura(models.Model):
    """HU21 · RF29 · RNF08 · CU13. Cómo se corrige una factura es la pregunta V02: no hay anular ni eliminar."""

    numero = models.PositiveIntegerField("N° de factura", unique=True)
    cliente = models.ForeignKey("clientes.Cliente", verbose_name="cliente", on_delete=models.PROTECT, related_name="facturas")
    rut_facturacion = models.CharField("RUT de facturación", max_length=12)
    razon_social = models.CharField("razón social", max_length=150)
    giro = models.CharField("giro", max_length=150)
    direccion_facturacion = models.CharField("dirección de facturación", max_length=200)
    fecha = models.DateField("fecha", default=timezone.localdate)
    neto = models.PositiveIntegerField("neto")
    iva = models.PositiveIntegerField("IVA")
    total = models.PositiveIntegerField("total")
    registrada_por = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="registrada por", on_delete=models.PROTECT,
                                       related_name="facturas_registradas")
    registrada_en = models.DateTimeField("registrada el", auto_now_add=True)

    class Meta:
        verbose_name = "factura"
        verbose_name_plural = "facturas"
        ordering = ["-numero"]

    def __str__(self):
        return f"Factura N° {self.numero}"


class LineaFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.PROTECT, related_name="lineas")
    servicio_realizado = models.ForeignKey("reservas.ServicioRealizado", on_delete=models.PROTECT, related_name="lineas_factura")
    descripcion = models.CharField("descripción", max_length=200)
    monto = models.PositiveIntegerField("monto")

    class Meta:
        verbose_name = "línea de factura"
        verbose_name_plural = "líneas de factura"
        ordering = ["id"]
