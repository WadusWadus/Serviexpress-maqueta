"""Base común (S0): auditoría, correlativos y control de versión. MAQUETA-SPEC 5.3, 5.5 y 5.6."""

from django.conf import settings
from django.db import models


class RegistroAuditoria(models.Model):
    """RNF06, RNF08 · Log de auditoría. Solo se escribe con core.auditoria.registrar()."""

    CREAR = "CREAR"
    MODIFICAR = "MODIFICAR"
    ANULAR = "ANULAR"
    ELIMINAR = "ELIMINAR"
    ACCESO_DENEGADO = "ACCESO_DENEGADO"
    LOGIN_FALLIDO = "LOGIN_FALLIDO"
    BLOQUEO = "BLOQUEO"
    OPERACIONES = [
        (CREAR, "Crear"),
        (MODIFICAR, "Modificar"),
        (ANULAR, "Anular"),
        (ELIMINAR, "Eliminar"),
        (ACCESO_DENEGADO, "Acceso denegado"),
        (LOGIN_FALLIDO, "Ingreso fallido"),
        (BLOQUEO, "Bloqueo de cuenta"),
    ]

    fecha_hora = models.DateTimeField("fecha y hora", auto_now_add=True, db_index=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="usuario", null=True, blank=True, on_delete=models.SET_NULL
    )
    operacion = models.CharField("operación", max_length=20, choices=OPERACIONES, db_index=True)
    entidad = models.CharField("entidad", max_length=50)
    entidad_id = models.CharField("identificador", max_length=50, blank=True)
    detalle = models.JSONField("detalle", null=True, blank=True)

    class Meta:
        verbose_name = "registro de auditoría"
        verbose_name_plural = "registros de auditoría"
        ordering = ["-fecha_hora", "-id"]

    def __str__(self):
        return f"{self.fecha_hora:%d-%m-%Y %H:%M} · {self.get_operacion_display()} · {self.entidad} {self.entidad_id}"


class Correlativo(models.Model):
    """RF20, RF22 · Numeración que nunca retrocede. Se usa con core.correlativos.siguiente()."""

    nombre = models.CharField("nombre", max_length=30, unique=True)
    ultimo = models.PositiveIntegerField("último número", default=0)

    class Meta:
        verbose_name = "correlativo"
        verbose_name_plural = "correlativos"

    def __str__(self):
        return f"{self.nombre}: {self.ultimo}"


class ConVersion(models.Model):
    """RNF23 · Aviso de conflicto de edición: cada modificación sube la versión en 1."""

    version = models.PositiveIntegerField("versión", default=1, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            self.version += 1
        super().save(*args, **kwargs)


class SeccionAyuda(models.Model):
    """HU03 · RF04 · Una sección del manual por módulo (los nombres de core.permisos)."""

    GENERAL = "general"

    modulo = models.CharField("módulo", max_length=30, unique=True,
                              help_text="Nombre del módulo (core.permisos) o «general» para el manual general.")
    titulo = models.CharField("título", max_length=100)
    contenido = models.TextField("contenido", help_text="Texto simple: una línea por paso.")
    orden = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        verbose_name = "sección de ayuda"
        verbose_name_plural = "secciones de ayuda"
        ordering = ["orden", "titulo"]

    def __str__(self):
        return self.titulo
