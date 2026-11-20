"""Área 5 · Abastecimiento. HU15 (proveedores), HU16 (órdenes) y HU18 (recepciones)."""

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from core.permisos import denegar, requiere_modulo
from personal.servicios import empleado_de

from . import servicios as srv
from .forms import BuscarOrdenForm, LineasOrdenFormSet, OrdenForm, OrdenModificarForm, ProveedorForm, RecepcionForm
from .models import OrdenPedido, Proveedor, Recepcion


# ---------------------------------------------------------------- HU15 · Proveedores

@requiere_modulo("abastecimiento")
def proveedores(request):
    """HU15 · RF19 · CU09 · Buscador por RUT, razón social o rubro."""
    q = request.GET.get("q", "").strip()
    lista = Proveedor.objects.all()
    if q:
        lista = lista.filter(Q(rut__icontains=q) | Q(razon_social__icontains=q) | Q(rubro__icontains=q))
    pagina = Paginator(lista, 50).get_page(request.GET.get("page"))
    return render(request, "abastecimiento/proveedores.html", {"page_obj": pagina, "q": q})


@requiere_modulo("abastecimiento")
def proveedor_nuevo(request):
    form = ProveedorForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        proveedor = form.save()
        messages.success(request, f"Proveedor {proveedor} registrado.")
        return redirect("abastecimiento:proveedor", pk=proveedor.pk)
    return render(request, "abastecimiento/proveedor_form.html", {"form": form, "titulo": "Nuevo proveedor"})


@requiere_modulo("abastecimiento")
def proveedor(request, pk):
    obj = get_object_or_404(Proveedor, pk=pk)
    return render(request, "abastecimiento/proveedor.html", {"proveedor": obj, "ordenes": obj.ordenes.all()[:20]})


@requiere_modulo("abastecimiento")
def proveedor_editar(request, pk):
    obj = get_object_or_404(Proveedor, pk=pk)
    form = ProveedorForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Proveedor actualizado.")
        return redirect("abastecimiento:proveedor", pk=obj.pk)
    return render(request, "abastecimiento/proveedor_form.html", {"form": form, "titulo": f"Editar proveedor {obj}", "proveedor": obj})


# ---------------------------------------------------------------- HU16 · Órdenes de pedido

def empleado_habilitado(request):
    """RF23 · Solo un empleado con la función «solicita productos» genera o corrige órdenes (flujo 2a)."""
    empleado = empleado_de(request.user)
    return empleado if empleado and empleado.solicita_productos else None


def denegar_no_habilitado(request):
    return denegar(request, "abastecimiento",
                   "Su cuenta no está asociada a un empleado habilitado para solicitar productos (RF23).")


@requiere_modulo("abastecimiento")
def ordenes(request):
    """HU16 · Lista con número, proveedor, fecha y estado."""
    q = request.GET.get("q", "").strip()
    lista = OrdenPedido.objects.select_related("proveedor", "creada_por").prefetch_related("lineas", "recepciones")
    if q:
        filtro = Q(proveedor__razon_social__icontains=q)
        if q.isdigit():
            filtro |= Q(numero=int(q))
        lista = lista.filter(filtro)
    pagina = Paginator(lista, 50).get_page(request.GET.get("page"))
    return render(request, "abastecimiento/ordenes.html", {"page_obj": pagina, "q": q})


@requiere_modulo("abastecimiento")
def orden_nueva(request):
    """HU16 · RF20, RF23 · RNF08 · CU10"""
    empleado = empleado_habilitado(request)
    if empleado is None:
        return denegar_no_habilitado(request)
    form = OrdenForm(request.POST or None)
    formset = LineasOrdenFormSet(request.POST or None, prefix="lineas")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        orden = srv.crear_orden(empleado, request.user, form.cleaned_data["proveedor"], formset.lineas(),
                                form.cleaned_data["observacion"])
        messages.success(request, f"Orden de pedido N° {orden.numero} generada.")
        return redirect("abastecimiento:orden", numero=orden.numero)
    return render(request, "abastecimiento/orden_form.html", {
        "form": form, "formset": formset, "titulo": "Nueva orden de pedido", "empleado": empleado,
        "traza": "HU16 · RF20, RF23 · RNF08 · CU10 · S4",
    })


@requiere_modulo("abastecimiento")
def orden(request, numero):
    """HU16 · Detalle imprimible."""
    obj = get_object_or_404(OrdenPedido.objects.select_related("proveedor", "creada_por"), numero=numero)
    return render(request, "abastecimiento/orden.html", {
        "orden": obj, "lineas": obj.lineas.select_related("producto"), "recepciones": obj.recepciones.all(),
    })


# ---------------------------------------------------------------- HU17 · Modificar o eliminar orden (S5)

def _orden_corregible(request, numero):
    """Devuelve (orden, empleado, respuesta). Si `respuesta` no es None, hay que devolverla."""
    obj = get_object_or_404(OrdenPedido, numero=numero)
    empleado = empleado_habilitado(request)
    if empleado is None:
        return obj, None, denegar_no_habilitado(request)
    if obj.tiene_recepciones:
        messages.error(request, srv.MENSAJE_CON_RECEPCIONES)
        return obj, empleado, redirect("abastecimiento:orden", numero=numero)
    return obj, empleado, None


@requiere_modulo("abastecimiento")
def orden_modificar(request, numero):
    """HU17 · RF21, RF23 · RNF08 · CU10"""
    obj, empleado, respuesta = _orden_corregible(request, numero)
    if respuesta:
        return respuesta
    inicial = [{"producto": l.producto, "cantidad": l.cantidad_solicitada} for l in obj.lineas.select_related("producto")]
    form = OrdenModificarForm(request.POST or None, orden=obj)
    formset = LineasOrdenFormSet(request.POST or None, prefix="lineas", initial=inicial)
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        try:
            srv.modificar_orden(obj, request.user, formset.lineas(), form.cleaned_data["observacion"])
        except srv.OrdenConRecepciones as error:
            messages.error(request, str(error))
        else:
            messages.success(request, f"Orden N° {numero} modificada; el cambio quedó en el log.")
        return redirect("abastecimiento:orden", numero=numero)
    return render(request, "abastecimiento/orden_form.html", {
        "form": form, "formset": formset, "titulo": f"Modificar orden N° {numero}", "empleado": empleado, "orden": obj,
        "traza": "HU17 · RF21, RF23 · RNF08 · CU10 · S5",
    })


@requiere_modulo("abastecimiento")
def orden_eliminar(request, numero):
    """HU17 · RF22, RF23 · RNF08 · CU10"""
    obj, _empleado, respuesta = _orden_corregible(request, numero)
    if respuesta:
        return respuesta
    if request.method == "POST":
        try:
            srv.eliminar_orden(obj, request.user)
        except srv.OrdenConRecepciones as error:
            messages.error(request, str(error))
            return redirect("abastecimiento:orden", numero=numero)
        messages.success(request, f"Orden N° {numero} eliminada. Su número no se volverá a usar.")
        return redirect("abastecimiento:ordenes")
    return render(request, "abastecimiento/orden_eliminar.html", {"orden": obj})


# ---------------------------------------------------------------- HU18 · Recepciones

@requiere_modulo("abastecimiento")
def recepcion_nueva(request):
    """HU18 · Paso 1: ingresar el número de la orden (flujo 1a si no existe)."""
    form = BuscarOrdenForm(request.GET or None)
    if form.is_valid():
        numero = form.cleaned_data["numero"]
        if OrdenPedido.objects.filter(numero=numero).exists():
            return redirect("abastecimiento:recepcionar", numero=numero)
        messages.error(request, f"La orden N° {numero} no existe.")
    return render(request, "abastecimiento/recepcion_buscar.html", {"form": form})


@requiere_modulo("abastecimiento")
def recepcionar(request, numero):
    """HU18 · RF24, RF25 · CU11 · Paso 2: lo recibido contra lo pendiente de la orden."""
    obj = get_object_or_404(OrdenPedido.objects.select_related("proveedor"), numero=numero)
    form = RecepcionForm(request.POST or None, orden=obj)
    advertencias = []
    if request.method == "POST" and form.is_valid():
        try:
            recepcion, advertencias = srv.registrar_recepcion(
                obj, request.user, form.cantidades(), form.extras(),
                confirmar_diferencias=request.POST.get("confirmar") == "1",
                observacion=form.cleaned_data["observacion"],
            )
        except (srv.ProductoNoSolicitado, srv.RecepcionInvalida) as error:
            messages.error(request, str(error))  # RF25: no se guarda nada
        else:
            if recepcion:
                texto = " con diferencias confirmadas" if advertencias else ""
                messages.success(request, f"Recepción registrada{texto} para la orden N° {numero}.")
                return redirect("abastecimiento:orden", numero=numero)
    return render(request, "abastecimiento/recepcionar.html", {"orden": obj, "form": form, "advertencias": advertencias})


@requiere_modulo("abastecimiento")
def recepciones(request):
    """HU18 · Historial de recepciones."""
    lista = Recepcion.objects.select_related("orden__proveedor", "recibida_por").prefetch_related("lineas__producto")
    pagina = Paginator(lista, 50).get_page(request.GET.get("page"))
    return render(request, "abastecimiento/recepciones.html", {"page_obj": pagina})
