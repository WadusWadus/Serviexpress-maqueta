"""Área 3 · Reservas y atención."""

from datetime import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone


class DiaFestivo(models.Model):
    """HU09 · RF12 · CU05"""

    fecha = models.DateField("fecha", unique=True,
                             error_messages={"unique": "Esa fecha ya está registrada como festiva."})
    descripcion = models.CharField("descripción", max_length=100)

    class Meta:
        verbose_name = "día festivo"
        verbose_name_plural = "días festivos"
        ordering = ["fecha"]

    def __str__(self):
        return f"{self.fecha:%d-%m-%Y} · {self.descripcion}"


class Reserva(models.Model):
    """HU08, HU10 · RF10, RF11, RF13 · CU04"""

    VIGENTE = "VIGENTE"
    ANULADA = "ANULADA"
    ATENDIDA = "ATENDIDA"
    ESTADOS = [(VIGENTE, "Vigente"), (ANULADA, "Anulada"), (ATENDIDA, "Atendida")]
    WEB = "WEB"
    LOCAL = "LOCAL"
    CANALES = [(WEB, "Internet"), (LOCAL, "En el local")]

    numero = models.AutoField("N° de reserva", primary_key=True)
    cliente = models.ForeignKey("clientes.Cliente", verbose_name="cliente", on_delete=models.PROTECT, related_name="reservas")
    servicio = models.ForeignKey("catalogo.Servicio", verbose_name="servicio", on_delete=models.PROTECT, related_name="reservas")
    fecha = models.DateField("fecha")
    hora_inicio = models.TimeField("hora")
    estado = models.CharField("estado", max_length=10, choices=ESTADOS, default=VIGENTE)
    canal = models.CharField("canal", max_length=10, choices=CANALES, default=WEB)
    creada_por = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="creada por", on_delete=models.PROTECT,
                                   related_name="reservas_creadas")
    creada_en = models.DateTimeField("creada el", auto_now_add=True)

    class Meta:
        verbose_name = "reserva"
        verbose_name_plural = "reservas"
        ordering = ["fecha", "hora_inicio"]
        constraints = [
            # 1 reserva vigente por bloque (MAQUETA-SPEC 5.7): dos personas no toman la misma hora (flujo 5a).
            models.UniqueConstraint(fields=["fecha", "hora_inicio"], condition=models.Q(estado="VIGENTE"),
                                    name="una_reserva_vigente_por_bloque"),
        ]

    def __str__(self):
        return f"Reserva N° {self.numero} · {self.fecha:%d-%m-%Y} {self.hora_inicio:%H:%M}"

    @property
    def inicio(self):
        return timezone.make_aware(datetime.combine(self.fecha, self.hora_inicio))

    @property
    def modificable(self):
        """HU10 · Solo reservas vigentes con fecha futura."""
        return self.estado == self.VIGENTE and self.inicio > timezone.now()


class ServicioRealizado(models.Model):
    """HU11 · RF14 · CU06 · Servicio ejecutado por un mecánico; queda pendiente de boleta o factura."""

    PENDIENTE = "PENDIENTE"
    DOCUMENTADO = "DOCUMENTADO"
    ESTADOS_DOCUMENTO = [(PENDIENTE, "Pendiente de documento"), (DOCUMENTADO, "Documentado")]

    cliente = models.ForeignKey("clientes.Cliente", verbose_name="cliente", on_delete=models.PROTECT,
                                related_name="servicios_realizados")
    servicio = models.ForeignKey("catalogo.Servicio", verbose_name="servicio", on_delete=models.PROTECT,
                                 related_name="realizados")
    reserva = models.ForeignKey(Reserva, verbose_name="reserva", null=True, blank=True, on_delete=models.PROTECT,
                                related_name="servicios_realizados",
                                help_text="Vacío si el cliente llegó sin reserva (flujo 1a).")
    fecha = models.DateField("fecha", default=timezone.localdate)
    empleado = models.ForeignKey("personal.Empleado", verbose_name="mecánico", on_delete=models.PROTECT,
                                 related_name="servicios_realizados")
    observacion = models.TextField("observación", blank=True)
    estado_documento = models.CharField("documento", max_length=12, choices=ESTADOS_DOCUMENTO, default=PENDIENTE)
    registrado_en = models.DateTimeField("registrado el", auto_now_add=True)

    class Meta:
        verbose_name = "servicio realizado"
        verbose_name_plural = "servicios realizados"
        ordering = ["-fecha", "-registrado_en"]

    def __str__(self):
        return f"{self.servicio} · {self.cliente.nombre_completo} · {self.fecha:%d-%m-%Y}"
