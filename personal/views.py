"""Área 4 · Personal. HU14 · RF18 · CU17."""

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from core.permisos import requiere_modulo

from .forms import EmpleadoForm
from .models import Empleado


@requiere_modulo("personal")
def lista(request):
    empleados = Empleado.objects.select_related("usuario")
    pagina = Paginator(empleados, 50).get_page(request.GET.get("page"))
    return render(request, "personal/lista.html", {"page_obj": pagina})


@requiere_modulo("personal")
def nuevo(request):
    form = EmpleadoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        empleado = form.save()
        messages.success(request, f"Empleado {empleado} registrado.")
        return redirect("personal:lista")
    return render(request, "personal/form.html", {"form": form, "titulo": "Nuevo empleado"})


@requiere_modulo("personal")
def editar(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    form = EmpleadoForm(request.POST or None, instance=empleado)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Empleado {empleado} actualizado.")
        return redirect("personal:lista")
    return render(request, "personal/form.html", {"form": form, "titulo": f"Editar empleado {empleado}"})
