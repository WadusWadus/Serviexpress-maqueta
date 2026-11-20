"""Área 7 · Informes y gestión."""

from django.conf import settings
from django.db import models
from django.utils import timezone


class VisitaWeb(models.Model):
    """HU24 · RF33 · CU16 · Una visita = una sesión por ruta por día."""

    fecha_hora = models.DateTimeField("fecha y hora", default=timezone.now, db_index=True)
    ruta = models.CharField("ruta", max_length=200)
    clave_sesion = models.CharField("sesión", max_length=40, db_index=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="usuario", null=True, blank=True,
                                on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "visita web"
        verbose_name_plural = "visitas web"
        ordering = ["-fecha_hora"]

    def __str__(self):
        return f"{self.fecha_hora:%d-%m-%Y %H:%M} {self.ruta}"
