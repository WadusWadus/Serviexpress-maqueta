from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Solo para depurar (regla 5 de la spec)."""

    list_display = ["username", "first_name", "last_name", "perfil", "is_active", "bloqueado_hasta"]
    list_filter = ["perfil", "is_active"]
    fieldsets = UserAdmin.fieldsets + (("SERVIEXPRESS", {"fields": ["perfil", "intentos_fallidos", "bloqueado_hasta"]}),)
