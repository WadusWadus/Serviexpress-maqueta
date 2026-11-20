"""Área 5 · Abastecimiento. HU15 (proveedores), HU16–HU17 (órdenes de pedido), HU18 (recepciones)."""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from core.models import ConVersion
from core.validadores import normalizar_rut, validar_rut

CANTIDAD_POSITIVA = MinValueValidator(Decimal("0.01"), message="La cantidad debe ser mayor que 0.")


class Proveedor(models.Model):
    """HU15 · RF19 · CU09"""

    rut = models.CharField("RUT", max_length=12, unique=True, validators=[validar_rut],
                           error_messages={"unique": "Ya existe un proveedor con ese RUT."})
    razon_social = models.CharField("razón social", max_length=150)
    nombre_contacto = models.CharField("nombre de contacto", max_length=100, blank=True)
    telefono = models.CharField("teléfono", max_length=20, blank=True)
    email = models.EmailField("correo", blank=True)
    rubro = models.CharField("rubro", max_length=100)
    activo = models.BooleanField("activo", default=True, help_text="Un proveedor inactivo no aparece al crear órdenes.")

    class Meta:
        verbose_name = "proveedor"
        verbose_name_plural = "proveedores"
        ordering = ["razon_social"]

    def __str__(self):
        return self.razon_social

    def save(self, *args, **kwargs):
        self.rut = normalizar_rut(self.rut)
        super().save(*args, **kwargs)


class OrdenPedido(ConVersion):
    """HU16, HU17 · RF20–RF23 · RNF08 · CU10"""

    SIN_RECEPCION = "Sin recepción"
    PARCIAL = "Recepción parcial"
    COMPLETA = "Recepcionada completa"

    numero = models.PositiveIntegerField("N° de orden", unique=True)
    proveedor = models.ForeignKey(Proveedor, verbose_name="proveedor", on_delete=models.PROTECT, related_name="ordenes")
    fecha = models.DateField("fecha", default=timezone.localdate)
    creada_por = models.ForeignKey("personal.Empleado", verbose_name="creada por", on_delete=models.PROTECT,
                                   related_name="ordenes_pedido")
    observacion = models.TextField("observación", blank=True)

    class Meta:
        verbose_name = "orden de pedido"
        verbose_name_plural = "órdenes de pedido"
        ordering = ["-numero"]

    def __str__(self):
        return f"Orden de pedido N° {self.numero}"

    @property
    def tiene_recepciones(self):
        return self.recepciones.exists()

    @property
    def estado(self):
        if not self.tiene_recepciones:
            return self.SIN_RECEPCION
        if all(l.cantidad_pendiente == 0 for l in self.lineas.all()):
            return self.COMPLETA
        return self.PARCIAL


class LineaOrden(models.Model):
    orden = models.ForeignKey(OrdenPedido, on_delete=models.CASCADE, related_name="lineas")
    producto = models.ForeignKey("catalogo.Producto", verbose_name="producto", on_delete=models.PROTECT)
    cantidad_solicitada = models.DecimalField("cantidad solicitada", max_digits=10, decimal_places=2,
                                              validators=[CANTIDAD_POSITIVA])

    class Meta:
        verbose_name = "línea de orden"
        verbose_name_plural = "líneas de orden"
        ordering = ["id"]
        constraints = [models.UniqueConstraint(fields=["orden", "producto"], name="producto_unico_por_orden")]

    def __str__(self):
        return f"{self.producto} × {self.cantidad_solicitada}"

    @property
    def cantidad_recibida(self):
        total = LineaRecepcion.objects.filter(recepcion__orden_id=self.orden_id, producto_id=self.producto_id).aggregate(
            total=Sum("cantidad"))["total"]
        return total or Decimal("0")

    @property
    def cantidad_pendiente(self):
        return max(Decimal("0"), self.cantidad_solicitada - self.cantidad_recibida)


class Recepcion(models.Model):
    """HU18 · RF24, RF25 · CU11"""

    orden = models.ForeignKey(OrdenPedido, verbose_name="orden", on_delete=models.PROTECT, related_name="recepciones")
    fecha = models.DateTimeField("fecha", default=timezone.now)
    recibida_por = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="recibida por", on_delete=models.PROTECT)
    observacion = models.TextField("observación", blank=True)

    class Meta:
        verbose_name = "recepción"
        verbose_name_plural = "recepciones"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"Recepción {self.pk} de la orden N° {self.orden.numero}"


class LineaRecepcion(models.Model):
    recepcion = models.ForeignKey(Recepcion, on_delete=models.CASCADE, related_name="lineas")
    producto = models.ForeignKey("catalogo.Producto", verbose_name="producto", on_delete=models.PROTECT)
    cantidad = models.DecimalField("cantidad", max_digits=10, decimal_places=2, validators=[CANTIDAD_POSITIVA])

    class Meta:
        verbose_name = "línea de recepción"
        verbose_name_plural = "líneas de recepción"
        ordering = ["id"]
