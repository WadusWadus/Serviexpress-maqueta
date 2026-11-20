"""Área 1 · Acceso y seguridad. MAQUETA-SPEC 5.1."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Usuario(AbstractUser):
    """RF01–RF03 · Usuario con perfil, intentos fallidos y bloqueo (RNF10)."""

    ADMIN = "ADMIN"
    ADMINISTRATIVO = "ADMINISTRATIVO"
    MECANICO = "MECANICO"
    CLIENTE = "CLIENTE"
    PERFILES = [
        (ADMIN, "Administrador"),
        (ADMINISTRATIVO, "Empleado Administrativo"),
        (MECANICO, "Mecánico"),
        (CLIENTE, "Cliente"),
    ]

    perfil = models.CharField("perfil", max_length=20, choices=PERFILES, default=CLIENTE)
    intentos_fallidos = models.PositiveSmallIntegerField("intentos fallidos", default=0)
    bloqueado_hasta = models.DateTimeField("bloqueado hasta", null=True, blank=True)

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["username"]

    def __str__(self):
        nombre = self.get_full_name()
        return f"{nombre} ({self.username})" if nombre else self.username

    def esta_bloqueado(self):
        return self.bloqueado_hasta is not None and self.bloqueado_hasta > timezone.now()
