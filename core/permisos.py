"""RF03, RNF06, RNF07 · Permisos por módulo (MAQUETA-SPEC 5.2).

La tabla MODULOS_POR_PERFIL es la única fuente de verdad. Las filas de cada módulo
se agregan en el sprint que lo construye.
"""

from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.shortcuts import render

from .auditoria import registrar
from .models import RegistroAuditoria

ADMIN = "ADMIN"
ADMINISTRATIVO = "ADMINISTRATIVO"
MECANICO = "MECANICO"
CLIENTE = "CLIENTE"

MODULOS_POR_PERFIL = {
    ADMIN: {
        "usuarios", "auditoria", "personal", "clientes", "festivos",  # S1
        "catalogo", "agenda",  # S2
        "atencion", "ventas",  # S3
        "abastecimiento",  # S4
        "fiado", "informes",  # S5
        "estadisticas_web", "ayuda",  # S6
    },
    ADMINISTRATIVO: {
        "clientes",  # S1
        "catalogo", "agenda",  # S2
        "ventas",  # S3
        "abastecimiento",  # S4
        "informes",  # S5
        "ayuda",  # S6
    },
    MECANICO: {
        "atencion",  # S3
        "ayuda",  # S6
    },
    CLIENTE: {
        "reserva_web",  # S2
        "ayuda",  # S6
    },
}


def tiene_modulo(usuario, modulo):
    """ADMIN accede a todos los módulos (RNF07); el resto, según la tabla."""
    if not usuario.is_authenticated:
        return False
    perfil = getattr(usuario, "perfil", None)
    if perfil == ADMIN:
        return True
    return modulo in MODULOS_POR_PERFIL.get(perfil, set())


def modulos_visibles(usuario):
    """Módulos que se muestran en el menú del perfil (los marcados en la tabla)."""
    if not usuario.is_authenticated:
        return set()
    return MODULOS_POR_PERFIL.get(getattr(usuario, "perfil", None), set())


def denegar(request, modulo="", motivo=""):
    """Respuesta 403 + registro ACCESO_DENEGADO en el log (RNF06)."""
    registrar(
        request.user,
        RegistroAuditoria.ACCESO_DENEGADO,
        "Modulo",
        modulo,
        {"ruta": request.get_full_path(), "metodo": request.method, "motivo": motivo},
    )
    return render(request, "core/acceso_denegado.html", {"motivo": motivo, "modulo": modulo}, status=403)


def requiere_modulo(modulo):
    """Decorador para vistas de función."""

    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not tiene_modulo(request.user, modulo):
                return denegar(request, modulo, "El perfil no tiene acceso a este módulo.")
            return vista(request, *args, **kwargs)

        envoltura.modulo = modulo
        return envoltura

    return decorador


class RequiereModuloMixin:
    """Lo mismo que @requiere_modulo, para vistas de clase. Definir `modulo` en la vista."""

    modulo = None

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not tiene_modulo(request.user, self.modulo):
            return denegar(request, self.modulo, "El perfil no tiene acceso a este módulo.")
        return super().dispatch(request, *args, **kwargs)
