"""RNF11 · Aviso de sesión cerrada por inactividad.

La sesión de Django expira a los 15 minutos (SESSION_COOKIE_AGE). Al ingresar se deja
además una cookie de marca; si vuelve una petición anónima con esa marca, la sesión
se cerró por inactividad y se avisa en la pantalla de ingreso.
"""

from django.contrib import messages

COOKIE_MARCA = "sx_sesion_activa"
MENSAJE_INACTIVIDAD = "Su sesión se cerró por inactividad."


def marcar_sesion(response):
    response.set_cookie(COOKIE_MARCA, "1", max_age=12 * 60 * 60, httponly=True, samesite="Lax")


def desmarcar_sesion(response):
    response.delete_cookie(COOKIE_MARCA, samesite="Lax")


class AvisoInactividadMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        expirada = COOKIE_MARCA in request.COOKIES and not request.user.is_authenticated
        if expirada:
            messages.warning(request, MENSAJE_INACTIVIDAD)
        response = self.get_response(request)
        if expirada:
            desmarcar_sesion(response)
        return response
