"""Área 6 · Ventas. HU19, HU20 (boletas) y HU21 (facturas) · CU12, CU13."""

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from clientes.models import Cliente
from clientes.views import buscar_clientes
from core.auditoria import historial
from core.permisos import requiere_modulo

from . import servicios as srv
from .forms import AnularBoletaForm, BoletaModificarForm, EmitirBoletaForm, FacturaForm
from .models import Boleta, Factura


def _elegir_cliente(request, plantilla_titulo, url_siguiente, traza):
    """Paso 1 de boleta y factura: buscar al cliente."""
    q = request.GET.get("q", "").strip()
    resultados = buscar_clientes(q)[:20] if q else []
    return render(request, "ventas/elegir_cliente.html", {
        "q": q, "resultados": resultados, "titulo": plantilla_titulo, "url_siguiente": url_siguiente, "traza": traza,
    })


# ---------------------------------------------------------------- HU19 · Generar boleta

@requiere_modulo("ventas")
def boletas(request):
    """HU19, HU20 · Lista con filtros por número, cliente y estado."""
    lista = Boleta.objects.select_related("cliente")
    numero, cliente, estado = (request.GET.get(k, "").strip() for k in ("numero", "cliente", "estado"))
    if numero.isdigit():
        lista = lista.filter(numero=int(numero))
    if cliente:
        lista = lista.filter(cliente__in=buscar_clientes(cliente))
    if estado:
        lista = lista.filter(estado=estado)
    pagina = Paginator(lista, 50).get_page(request.GET.get("page"))
    return render(request, "ventas/boletas.html", {
        "page_obj": pagina, "numero": numero, "cliente": cliente, "estado": estado, "estados": Boleta.ESTADOS,
    })


@requiere_modulo("ventas")
def boleta_nueva(request):
    """HU19 · RF26 · CU12 · Paso 1: buscar cliente; paso 2 (?cliente=): marcar servicios y confirmar."""
    cliente_id = request.GET.get("cliente")
    if not cliente_id:
        return _elegir_cliente(request, "Nueva boleta", "ventas:boleta_nueva", "HU19 · RF26 · CU12 · S3")
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    pendientes = srv.servicios_pendientes(cliente)
    form = EmitirBoletaForm(request.POST or None, pendientes=pendientes, cliente=cliente)
    if request.method == "POST" and form.is_valid():
        try:
            # Se lee del POST y no solo del formulario: si alguien fuerza «fiada» para un cliente
            # no habilitado, el servidor lo rechaza (HU07).
            fiada = request.POST.get("fiada") in ("on", "true", "1")
            boleta = srv.emitir_boleta(cliente, form.cleaned_data["servicios"], request.user,
                                       form.cleaned_data["observacion"], fiada=fiada)
        except srv.VentaNoPermitida as error:
            messages.error(request, str(error))
        else:
            messages.success(request, f"Boleta N° {boleta.numero} emitida por {boleta.total:,} pesos.".replace(",", "."))
            return redirect("ventas:boleta", numero=boleta.numero)
    return render(request, "ventas/documento_nuevo.html", {
        "form": form, "cliente": cliente, "pendientes": pendientes, "tipo": "boleta",
        "traza": "HU19 · RF26 · RNF08 · CU12 · S3",
    })


@requiere_modulo("ventas")
def boleta(request, numero):
    """HU19 · Vista imprimible, con historial de cambios (HU20)."""
    documento = get_object_or_404(Boleta.objects.select_related("cliente", "emitida_por", "anulada_por"), numero=numero)
    return render(request, "ventas/boleta.html", {
        "boleta": documento, "lineas": documento.lineas.all(), "historial": historial("Boleta", numero),
    })


# ---------------------------------------------------------------- HU20 · Modificar o anular boleta

@requiere_modulo("ventas")
def boleta_modificar(request, numero):
    """HU20 · RF27 · RNF08 · CU12 (extend)"""
    documento = get_object_or_404(Boleta, numero=numero)
    if documento.anulada:
        messages.error(request, "Una boleta anulada no se puede modificar.")
        return redirect("ventas:boleta", numero=numero)
    form = BoletaModificarForm(request.POST or None, boleta=documento)
    if request.method == "POST" and form.is_valid():
        _, cambios = srv.modificar_boleta(documento, request.user, form.cleaned_data["observacion"], form.montos())
        messages.success(request, "Boleta modificada; el cambio quedó en el historial." if cambios else "No hubo cambios.")
        return redirect("ventas:boleta", numero=numero)
    return render(request, "ventas/boleta_modificar.html", {"form": form, "boleta": documento})


@requiere_modulo("ventas")
def boleta_anular(request, numero):
    """HU20 · RF28 · RNF08 · CU12 (extend)"""
    documento = get_object_or_404(Boleta, numero=numero)
    if documento.anulada:
        messages.error(request, "La boleta ya está anulada.")
        return redirect("ventas:boleta", numero=numero)
    form = AnularBoletaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        srv.anular_boleta(documento, request.user, form.cleaned_data["motivo"])
        messages.success(request, f"Boleta N° {numero} anulada. Sus servicios vuelven a estar pendientes.")
        return redirect("ventas:boleta", numero=numero)
    return render(request, "ventas/boleta_anular.html", {"form": form, "boleta": documento})


# ---------------------------------------------------------------- HU21 · Registrar factura

@requiere_modulo("ventas")
def facturas(request):
    lista = Factura.objects.select_related("cliente")
    q = request.GET.get("q", "").strip()
    if q:
        filtro = Q(cliente__in=buscar_clientes(q)) | Q(razon_social__icontains=q) | Q(rut_facturacion__icontains=q)
        if q.isdigit():
            filtro |= Q(numero=int(q))
        lista = lista.filter(filtro)
    pagina = Paginator(lista, 50).get_page(request.GET.get("page"))
    return render(request, "ventas/facturas.html", {"page_obj": pagina, "q": q})


@requiere_modulo("ventas")
def factura_nueva(request):
    """HU21 · RF29 · CU13 · cliente → servicios pendientes → datos de facturación → confirmar."""
    cliente_id = request.GET.get("cliente")
    if not cliente_id:
        return _elegir_cliente(request, "Nueva factura", "ventas:factura_nueva", "HU21 · RF29 · CU13 · S3")
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    pendientes = srv.servicios_pendientes(cliente)
    inicial = {"rut_facturacion": cliente.rut, "razon_social": cliente.nombre_completo,
               "direccion_facturacion": cliente.direccion}
    form = FacturaForm(request.POST or None, pendientes=pendientes, initial=inicial)
    if request.method == "POST" and form.is_valid():
        datos = {k: form.cleaned_data[k] for k in ("rut_facturacion", "razon_social", "giro", "direccion_facturacion")}
        try:
            factura = srv.registrar_factura(cliente, form.cleaned_data["servicios"], request.user, datos)
        except srv.VentaNoPermitida as error:
            messages.error(request, str(error))
        else:
            messages.success(request, f"Factura N° {factura.numero} registrada.")
            return redirect("ventas:factura", numero=factura.numero)
    return render(request, "ventas/documento_nuevo.html", {
        "form": form, "cliente": cliente, "pendientes": pendientes, "tipo": "factura",
        "traza": "HU21 · RF29 · RNF08 · CU13 · S3",
    })


@requiere_modulo("ventas")
def factura(request, numero):
    documento = get_object_or_404(Factura.objects.select_related("cliente", "registrada_por"), numero=numero)
    return render(request, "ventas/factura.html", {"factura": documento, "lineas": documento.lineas.all()})
