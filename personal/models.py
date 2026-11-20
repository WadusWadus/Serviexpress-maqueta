"""Área 4 · Personal. HU14 · RF18 · CU17."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.validadores import normalizar_rut, validar_rut


class Empleado(models.Model):
    rut = models.CharField("RUT", max_length=12, unique=True, validators=[validar_rut],
                           error_messages={"unique": "Ya existe un empleado con ese RUT."})
    nombres = models.CharField("nombres", max_length=100)
    apellidos = models.CharField("apellidos", max_length=100)
    telefono = models.CharField("teléfono", max_length=20, blank=True)
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name="cuenta de usuario", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="empleado",
        help_text="Opcional: un empleado puede no tener cuenta en el sistema.",
    )
    solicita_productos = models.BooleanField("solicita productos", default=False,
                                             help_text="Puede generar órdenes de pedido (RF23).")
    ejecuta_servicios = models.BooleanField("ejecuta servicios", default=False,
                                            help_text="Puede registrar servicios realizados (C07).")
    activo = models.BooleanField("activo", default=True)

    class Meta:
        verbose_name = "empleado"
        verbose_name_plural = "empleados"
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return self.nombre_completo

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    def clean(self):
        if not (self.solicita_productos or self.ejecuta_servicios):
            raise ValidationError("Marque al menos una función: solicitar productos o ejecutar servicios.")

    def save(self, *args, **kwargs):
        self.rut = normalizar_rut(self.rut)
        super().save(*args, **kwargs)
