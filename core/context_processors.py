from django.conf import settings

from .ayuda import seccion_para
from .menu import menu_para
from .permisos import modulos_visibles


def serviexpress(request):
    """Menú según el perfil (RF03), modo presentación de curso y ayuda contextual (HU03)."""
    usuario = getattr(request, "user", None)
    menu = menu_para(modulos_visibles(usuario), request.path) if usuario is not None else []
    return {"menu": menu, "demo": settings.DEMO, "ayuda": _Perezoso(lambda: seccion_para(request))}


class _Perezoso:
    """Solo consulta la sección de ayuda si la plantilla la usa."""

    def __init__(self, funcion):
        self._funcion, self._hecho, self._valor = funcion, False, None

    def _obtener(self):
        if not self._hecho:
            self._valor, self._hecho = self._funcion(), True
        return self._valor

    def __bool__(self):
        return self._obtener() is not None

    def __getattr__(self, nombre):
        return getattr(self._obtener(), nombre)
