"""Área 1 · Acceso y seguridad: HU01 (ingreso) y HU02 (cuentas y perfiles)."""

from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_not_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core.auditoria import registrar
from core.middleware import desmarcar_sesion, marcar_sesion
from core.models import RegistroAuditoria
from core.permisos import requiere_modulo

from .forms import IngresoForm, UsuarioCrearForm, UsuarioEditarForm
from .models import Usuario

MENSAJE_INCORRECTO = "Usuario o contraseña incorrectos."


def _mensaje_bloqueo():
    return f"Cuenta bloqueada por {settings.SERVIEXPRESS['MINUTOS_BLOQUEO']} minutos por intentos fallidos."


def _destino_seguro(request):
    destino = request.POST.get("next") or request.GET.get("next")
    if destino and url_has_allowed_host_and_scheme(destino, {request.get_host()}, request.is_secure()):
        return destino
    return None


@login_not_required
def ingresar(request):
    """HU01 · RF01 · RNF05, RNF10, RNF11 · CU01"""
    if request.user.is_authenticated:
        return redirect("core:panel")
    form = IngresoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        nombre = form.cleaned_data["usuario"]
        cuenta = Usuario.objects.filter(username=nombre).first()
        if cuenta and cuenta.esta_bloqueado():
            messages.error(request, _mensaje_bloqueo())
        else:
            usuario = authenticate(request, username=nombre, password=form.cleaned_data["contrasena"])
            if usuario is not None:
                usuario.intentos_fallidos = 0
                usuario.bloqueado_hasta = None
                usuario.save(update_fields=["intentos_fallidos", "bloqueado_hasta"])
                login(request, usuario)
                respuesta = redirect(_destino_seguro(request) or "core:panel")
                marcar_sesion(respuesta)
                return respuesta
            _registrar_fallo(request, nombre, cuenta)
    return render(request, "cuentas/ingresar.html", {"form": form, "next": _destino_seguro(request) or ""})


def _registrar_fallo(request, nombre, cuenta):
    """RNF10 · Suma el intento fallido y bloquea al 5° consecutivo."""
    registrar(cuenta, RegistroAuditoria.LOGIN_FALLIDO, "Usuario", nombre, {"usuario": nombre})
    if cuenta is None or not cuenta.is_active:
        messages.error(request, MENSAJE_INCORRECTO)
        return
    cuenta.intentos_fallidos += 1
    if cuenta.intentos_fallidos >= settings.SERVIEXPRESS["MAX_INTENTOS_LOGIN"]:
        cuenta.bloqueado_hasta = timezone.now() + timedelta(minutes=settings.SERVIEXPRESS["MINUTOS_BLOQUEO"])
        cuenta.intentos_fallidos = 0
        registrar(cuenta, RegistroAuditoria.BLOQUEO, "Usuario", nombre,
                  {"bloqueado_hasta": cuenta.bloqueado_hasta})
        messages.error(request, _mensaje_bloqueo())
    else:
        messages.error(request, MENSAJE_INCORRECTO)
    cuenta.save(update_fields=["intentos_fallidos", "bloqueado_hasta"])


@login_not_required
@require_POST
def salir(request):
    """HU01 · Cierra la sesión."""
    logout(request)
    messages.info(request, "Sesión cerrada.")
    respuesta = redirect("core:inicio")
    desmarcar_sesion(respuesta)
    return respuesta


@requiere_modulo("usuarios")
def lista_usuarios(request):
    """HU02 · RF02, RF03 · CU02"""
    usuarios = Usuario.objects.all().order_by("perfil", "username")
    perfil = request.GET.get("perfil", "")
    if perfil:
        usuarios = usuarios.filter(perfil=perfil)
    pagina = Paginator(usuarios, 50).get_page(request.GET.get("page"))
    return render(request, "cuentas/usuarios.html", {
        "page_obj": pagina, "perfiles": Usuario.PERFILES, "perfil": perfil,
    })


@requiere_modulo("usuarios")
def nuevo_usuario(request):
    """HU02 · RF02"""
    form = UsuarioCrearForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        messages.success(request, f"Cuenta «{usuario.username}» creada con perfil {usuario.get_perfil_display()}.")
        return redirect("cuentas:usuarios")
    return render(request, "cuentas/usuario_form.html", {"form": form, "titulo": "Nueva cuenta"})


@requiere_modulo("usuarios")
def editar_usuario(request, pk):
    """HU02 · RF02, RF03"""
    usuario = get_object_or_404(Usuario, pk=pk)
    form = UsuarioEditarForm(request.POST or None, instance=usuario)
    if request.method == "POST" and form.is_valid():
        if usuario == request.user and not form.cleaned_data["is_active"]:
            form.add_error("is_active", "No puede desactivar su propia cuenta.")
        else:
            form.save()
            messages.success(request, f"Cuenta «{usuario.username}» actualizada.")
            return redirect("cuentas:usuarios")
    return render(request, "cuentas/usuario_form.html", {
        "form": form, "titulo": f"Editar cuenta «{usuario.username}»", "usuario_editado": usuario,
    })


@requiere_modulo("usuarios")
def desactivar_usuario(request, pk):
    """HU02 · RF02 · Las cuentas no se borran: se desactivan."""
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == "POST":
        if usuario == request.user:
            messages.error(request, "No puede desactivar su propia cuenta.")
        else:
            usuario.is_active = False
            usuario.save(update_fields=["is_active"])
            messages.success(request, f"Cuenta «{usuario.username}» desactivada.")
        return redirect("cuentas:usuarios")
    return render(request, "cuentas/usuario_desactivar.html", {"usuario_editado": usuario})
