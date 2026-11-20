"""Área 2 · Clientes. HU04, HU05 · RF05, RF06 · CU03."""

from django.conf import settings
from django.db import models

from core.models import ConVersion
from core.validadores import normalizar_rut, validar_rut


class ClienteQuerySet(models.QuerySet):
    def habilitados_fiado(self):
        """HU06 · RF07 · Solo estos clientes tienen la opción de venta fiada."""
        return self.filter(fiado_habilitado=True)


class Cliente(ConVersion):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name="cuenta de usuario", on_delete=models.PROTECT, related_name="cliente"
    )
    rut = models.CharField("RUT", max_length=12, unique=True, validators=[validar_rut],
                           error_messages={"unique": "Ya existe un cliente con ese RUT."})
    nombres = models.CharField("nombres", max_length=100)
    apellidos = models.CharField("apellidos", max_length=100)
    telefono = models.CharField("teléfono", max_length=20, blank=True)
    email = models.EmailField("correo", blank=True)
    direccion = models.CharField("dirección", max_length=200, blank=True)
    fecha_registro = models.DateTimeField("fecha de registro", auto_now_add=True)
    fiado_habilitado = models.BooleanField("habilitado para fiado", default=False)  # HU06 · RF07 (S5)

    objects = ClienteQuerySet.as_manager()

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return f"{self.nombre_completo} ({self.rut})"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    def save(self, *args, **kwargs):
        self.rut = normalizar_rut(self.rut)
        super().save(*args, **kwargs)

    @property
    def saldo_fiado(self):
        """HU07 · RF09 · Saldo = suma de los movimientos de fiado."""
        return self.movimientos_fiado.aggregate(total=models.Sum("monto"))["total"] or 0


class MovimientoFiado(models.Model):
    """HU07 · RF08, RF09 · CU14. Positivo = deuda; negativo = reverso por anulación o ajuste.

    No hay registro de pagos: la cobranza está fuera del alcance (1.2).
    """

    cliente = models.ForeignKey(Cliente, verbose_name="cliente", on_delete=models.PROTECT, related_name="movimientos_fiado")
    boleta = models.ForeignKey("ventas.Boleta", verbose_name="boleta", on_delete=models.PROTECT, related_name="movimientos_fiado")
    fecha = models.DateTimeField("fecha", auto_now_add=True)
    monto = models.IntegerField("monto")
    descripcion = models.CharField("descripción", max_length=200)

    class Meta:
        verbose_name = "movimiento de fiado"
        verbose_name_plural = "movimientos de fiado"
        ordering = ["fecha", "id"]

    def __str__(self):
        return f"{self.cliente.nombre_completo}: {self.monto} ({self.descripcion})"
