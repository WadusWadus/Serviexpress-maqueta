"""Área 4 · Catálogo. HU12 · RF15, RF16 · CU07 y HU13 · RF17 · CU08."""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from core.models import ConVersion


class ProductoQuerySet(models.QuerySet):
    def activos(self):
        return self.filter(activo=True)


class Producto(models.Model):
    """HU13 · RF17"""

    UNIDADES = [("UNIDAD", "unidad"), ("LITRO", "litro"), ("KILO", "kilo"), ("METRO", "metro"), ("JUEGO", "juego")]

    codigo = models.CharField("código", max_length=30, unique=True,
                              error_messages={"unique": "Ya existe un producto con ese código."})
    descripcion = models.CharField("descripción", max_length=150)
    unidad = models.CharField("unidad", max_length=10, choices=UNIDADES, default="UNIDAD")
    activo = models.BooleanField("activo", default=True,
                                 help_text="Un producto desactivado no aparece al armar servicios ni órdenes.")

    objects = ProductoQuerySet.as_manager()

    class Meta:
        verbose_name = "producto"
        verbose_name_plural = "productos"
        ordering = ["codigo"]

    def __str__(self):
        return f"{self.codigo} · {self.descripcion}"

    def save(self, *args, **kwargs):
        self.codigo = self.codigo.strip().upper()
        super().save(*args, **kwargs)


class ServicioQuerySet(models.QuerySet):
    def reservables(self):
        """HU12 · Lo usa la reserva (HU08): solo servicios activos."""
        return self.filter(activo=True)


class Servicio(ConVersion):
    """HU12 · RF15, RF16 · El precio es condición necesaria para la boleta (CU12, paso 4)."""

    nombre = models.CharField("nombre", max_length=100, unique=True,
                              error_messages={"unique": "Ya existe un servicio con ese nombre."})
    descripcion = models.TextField("descripción", blank=True)
    precio = models.PositiveIntegerField("precio (pesos)")
    duracion_bloques = models.PositiveSmallIntegerField(
        "duración (bloques)", default=1, validators=[MinValueValidator(1)],
        help_text="Referencial: en la maqueta cada reserva ocupa un bloque (# DEMO: pendiente V07).",
    )
    activo = models.BooleanField("activo", default=True, help_text="Un servicio desactivado no se puede reservar.")
    productos = models.ManyToManyField(Producto, through="ServicioProducto", related_name="servicios", blank=True)

    objects = ServicioQuerySet.as_manager()

    class Meta:
        verbose_name = "servicio"
        verbose_name_plural = "servicios"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class ServicioProducto(models.Model):
    """HU12 · RF16 · Productos que usa cada servicio."""

    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name="lineas_producto")
    producto = models.ForeignKey(Producto, verbose_name="producto", on_delete=models.PROTECT)
    cantidad = models.DecimalField(
        "cantidad", max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"), message="La cantidad debe ser mayor que 0.")],
    )

    class Meta:
        verbose_name = "producto del servicio"
        verbose_name_plural = "productos del servicio"
        constraints = [models.UniqueConstraint(fields=["servicio", "producto"], name="servicio_producto_unico",
                                               violation_error_message="El producto ya está en el servicio.")]

    def __str__(self):
        return f"{self.producto} × {self.cantidad}"
