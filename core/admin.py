from django.contrib import admin

from .models import Correlativo, RegistroAuditoria, SeccionAyuda


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    """Solo lectura: el log no se edita ni se borra."""

    list_display = ["fecha_hora", "usuario", "operacion", "entidad", "entidad_id"]
    list_filter = ["operacion", "entidad"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Correlativo)
admin.site.register(SeccionAyuda)
