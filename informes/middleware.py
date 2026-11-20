"""HU24 · RF33 · Registro de visitas a las páginas públicas y de reserva.

No registra archivos estáticos ni pantallas internas. Una visita = una sesión por ruta por día
(así las recargas no cuentan).
"""

from django.utils import timezone

from .models import VisitaWeb

RUTAS_EXACTAS = {"/", "/cuentas/ingresar/"}
PREFIJO_RESERVAS = "/reservas/"
EXCLUIDAS = ("/reservas/festivos/",)  # pantalla interna del Administrador


def es_pagina_publica(ruta):
    if ruta in RUTAS_EXACTAS:
        return True
    return ruta.startswith(PREFIJO_RESERVAS) and not ruta.startswith(EXCLUIDAS)


class RegistroVisitasMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        respuesta = self.get_response(request)
        if request.method == "GET" and respuesta.status_code == 200 and es_pagina_publica(request.path):
            self._registrar(request)
        return respuesta

    @staticmethod
    def _registrar(request):
        if not request.session.session_key:
            request.session.save()
        clave = request.session.session_key
        hoy = timezone.localdate()
        inicio = timezone.make_aware(timezone.datetime.combine(hoy, timezone.datetime.min.time()))
        if VisitaWeb.objects.filter(clave_sesion=clave, ruta=request.path, fecha_hora__gte=inicio).exists():
            return
        usuario = request.user if request.user.is_authenticated else None
        VisitaWeb.objects.create(ruta=request.path, clave_sesion=clave, usuario=usuario)
