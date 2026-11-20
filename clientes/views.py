"""Área 2 · Clientes. HU04, HU05 · RF05, RF06 · CU03."""

import re

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.auditoria import registrar
from core.models import RegistroAuditoria
from core.permisos import requiere_modulo
from core.validadores import normalizar_rut

from .forms import ClienteEditarForm, ClienteNuevoForm
from .models import Cliente


def buscar_clientes(texto, clientes=None):
    """Búsqueda por RUT, nombre, apellido o usuario (cada palabra debe coincidir). La reutilizan reservas y ventas."""
    clientes = Cliente.objects.all() if clientes is None else clientes
    for parte in (texto or "").split():
        filtro = Q(nombres__icontains=parte) | Q(apellidos__icontains=parte) | Q(usuario__username__icontains=parte)
        cifras = re.sub(r"[^0-9kK]", "", parte).upper()
        if cifras:
            filtro |= Q(rut__icontains=cifras) | Q(rut__icontains=normalizar_rut(parte))
        clientes = clientes.filter(filtro)
    return clientes


@requiere_modulo("clientes")
def lista(request):
    """HU05 · RF06 · RNF02 · Lista paginada de 50 con buscador."""
    q = request.GET.get("q", "")
    clientes = buscar_clientes(q).select_related("usuario")
    pagina = Paginator(clientes, 50).get_page(request.GET.get("page"))
    return render(request, "clientes/lista.html", {"page_obj": pagina, "q": q})


@requiere_modulo("clientes")
def nuevo(request):
    """HU04 · RF05 · CU03"""
    form = ClienteNuevoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cliente = form.save()
        messages.success(request, f"Ficha de {cliente.nombre_completo} registrada. Ya puede ingresar a la web con el usuario «{cliente.usuario.username}».")
        return redirect("clientes:ficha", pk=cliente.pk)
    return render(request, "clientes/form.html", {"form": form, "titulo": "Nueva ficha de cliente", "traza": "HU04 · RF05 · CU03 · S1"})


@requiere_modulo("clientes")
def ficha(request, pk):
    """HU05 · RF06 · CU03"""
    cliente = get_object_or_404(Cliente.objects.select_related("usuario"), pk=pk)
    return render(request, "clientes/ficha.html", {"cliente": cliente})


@requiere_modulo("clientes")
def editar(request, pk):
    """HU05 · RF06 · RNF23 · CU03"""
    cliente = get_object_or_404(Cliente, pk=pk)
    form = ClienteEditarForm(request.POST or None, instance=cliente)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Ficha actualizada.")
        return redirect("clientes:ficha", pk=cliente.pk)
    return render(request, "clientes/form.html", {
        "form": form, "titulo": f"Editar ficha de {cliente.nombre_completo} ({cliente.rut})",
        "traza": "HU05 · RF06 · RNF23 · CU03 · S1", "cliente": cliente,
    })


# ---------------------------------------------------------------- HU06 · Habilitar fiado (S5)

@requiere_modulo("fiado")
def fiado(request):
    """HU06 · RF07 · CU14 · Interruptor «Habilitado para fiado» y saldo de cada habilitado (HU07)."""
    q = request.GET.get("q", "")
    clientes = buscar_clientes(q).annotate(saldo=Coalesce(Sum("movimientos_fiado__monto"), 0))
    pagina = Paginator(clientes, 50).get_page(request.GET.get("page"))
    return render(request, "clientes/fiado.html", {"page_obj": pagina, "q": q})


@requiere_modulo("fiado")
@require_POST
def fiado_cambiar(request, pk):
    """HU06 · RF07 · Solo el Administrador cambia la habilitación."""
    cliente = get_object_or_404(Cliente, pk=pk)
    anterior = cliente.fiado_habilitado
    cliente.fiado_habilitado = not anterior
    cliente.save()
    registrar(request.user, RegistroAuditoria.MODIFICAR, "Cliente", cliente.pk,
              {"cambios": {"fiado_habilitado": {"anterior": anterior, "nuevo": cliente.fiado_habilitado}}})
    estado = "habilitado" if cliente.fiado_habilitado else "deshabilitado"
    messages.success(request, f"{cliente.nombre_completo} quedó {estado} para comprar fiado.")
    return redirect(request.POST.get("volver") or "clientes:fiado")


# ---------------------------------------------------------------- HU07 · Saldo de fiado (S5)

@requiere_modulo("clientes")
def saldo(request, pk):
    """HU07 · RF09 · CU14 · Saldo y detalle de movimientos."""
    cliente = get_object_or_404(Cliente, pk=pk)
    movimientos = cliente.movimientos_fiado.select_related("boleta")
    return render(request, "clientes/saldo.html", {"cliente": cliente, "movimientos": movimientos})
