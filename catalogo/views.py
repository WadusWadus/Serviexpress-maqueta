"""Área 4 · Catálogo. HU12 (servicios con productos) y HU13 (productos)."""

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from core.permisos import requiere_modulo

from .forms import ProductoForm, ProductosDelServicioFormSet, ServicioForm
from .models import Producto, Servicio


# ---------------------------------------------------------------- HU13 · Productos

@requiere_modulo("catalogo")
def productos(request):
    """HU13 · RF17 · CU08"""
    q = request.GET.get("q", "").strip()
    lista = Producto.objects.all()
    if q:
        lista = lista.filter(Q(codigo__icontains=q) | Q(descripcion__icontains=q))
    pagina = Paginator(lista, 50).get_page(request.GET.get("page"))
    return render(request, "catalogo/productos.html", {"page_obj": pagina, "q": q})


@requiere_modulo("catalogo")
def producto_nuevo(request):
    form = ProductoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        producto = form.save()
        messages.success(request, f"Producto {producto} registrado.")
        return redirect("catalogo:productos")
    return render(request, "catalogo/producto_form.html", {"form": form, "titulo": "Nuevo producto"})


@requiere_modulo("catalogo")
def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST or None, instance=producto)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Producto actualizado.")
        return redirect("catalogo:productos")
    return render(request, "catalogo/producto_form.html", {"form": form, "titulo": f"Editar producto {producto.codigo}"})


@requiere_modulo("catalogo")
def producto_desactivar(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        producto.activo = False
        producto.save(update_fields=["activo"])
        messages.success(request, f"Producto {producto.codigo} desactivado. Se reactiva desde «Editar».")
        return redirect("catalogo:productos")
    return render(request, "catalogo/confirmar_desactivar.html", {
        "objeto": producto, "objeto_nombre": producto.descripcion, "volver": "catalogo:productos", "traza": "HU13 · RF17 · CU08 · S2",
        "aviso": "No aparecerá al armar servicios ni órdenes de pedido.",
    })


# ---------------------------------------------------------------- HU12 · Servicios

@requiere_modulo("catalogo")
def servicios(request):
    """HU12 · RF15, RF16 · CU07"""
    q = request.GET.get("q", "").strip()
    lista = Servicio.objects.prefetch_related("lineas_producto__producto")
    if q:
        lista = lista.filter(nombre__icontains=q)
    pagina = Paginator(lista, 50).get_page(request.GET.get("page"))
    return render(request, "catalogo/servicios.html", {"page_obj": pagina, "q": q})


@requiere_modulo("catalogo")
def servicio_detalle(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    return render(request, "catalogo/servicio_detalle.html", {
        "servicio": servicio, "lineas": servicio.lineas_producto.select_related("producto"),
    })


def _guardar_servicio(request, servicio=None):
    form = ServicioForm(request.POST or None, instance=servicio)
    formset = ProductosDelServicioFormSet(request.POST or None, instance=servicio or Servicio(), prefix="productos")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            guardado = form.save()
            formset.instance = guardado
            formset.save()
        messages.success(request, f"Servicio «{guardado}» guardado.")
        return redirect("catalogo:servicio_detalle", pk=guardado.pk)
    titulo = f"Editar servicio «{servicio}»" if servicio else "Nuevo servicio"
    return render(request, "catalogo/servicio_form.html", {"form": form, "formset": formset, "titulo": titulo, "servicio": servicio})


@requiere_modulo("catalogo")
def servicio_nuevo(request):
    return _guardar_servicio(request)


@requiere_modulo("catalogo")
def servicio_editar(request, pk):
    return _guardar_servicio(request, get_object_or_404(Servicio, pk=pk))


@requiere_modulo("catalogo")
def servicio_desactivar(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    if request.method == "POST":
        servicio.activo = False
        servicio.save()
        messages.success(request, f"Servicio «{servicio}» desactivado: ya no aparece al reservar.")
        return redirect("catalogo:servicios")
    return render(request, "catalogo/confirmar_desactivar.html", {
        "objeto": servicio, "objeto_nombre": servicio.nombre, "volver": "catalogo:servicios", "traza": "HU12 · RF15 · CU07 · S2",
        "aviso": "Los clientes ya no podrán reservarlo. Se reactiva desde «Editar».",
    })
