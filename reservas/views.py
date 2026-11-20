"""Área 3 · Reservas y atención."""

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.permisos import requiere_modulo

from .forms import DiaFestivoForm
from .models import DiaFestivo


# ---------------------------------------------------------------- HU09 · Días festivos

@requiere_modulo("festivos")
def festivos(request):
    """HU09 · RF12 · CU05 · Lista por año con selector."""
    hoy = timezone.localdate()
    try:
        anio = int(request.GET.get("anio", hoy.year))
    except ValueError:
        anio = hoy.year
    anios = sorted({hoy.year, hoy.year + 1, anio} | set(d.year for d in DiaFestivo.objects.dates("fecha", "year")))
    return render(request, "reservas/festivos.html", {
        "festivos": DiaFestivo.objects.filter(fecha__year=anio), "anio": anio, "anios": anios,
    })


@requiere_modulo("festivos")
def festivo_nuevo(request):
    form = DiaFestivoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        festivo = form.save()
        messages.success(request, f"Festivo {festivo} registrado: ese día no se ofrece para reservar.")
        return redirect(f"{_url_festivos()}?anio={festivo.fecha.year}")
    return render(request, "reservas/festivo_form.html", {"form": form, "titulo": "Nuevo día festivo"})


@requiere_modulo("festivos")
def festivo_editar(request, pk):
    festivo = get_object_or_404(DiaFestivo, pk=pk)
    form = DiaFestivoForm(request.POST or None, instance=festivo)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Festivo actualizado.")
        return redirect(f"{_url_festivos()}?anio={festivo.fecha.year}")
    return render(request, "reservas/festivo_form.html", {"form": form, "titulo": f"Editar festivo {festivo}"})


@requiere_modulo("festivos")
def festivo_eliminar(request, pk):
    festivo = get_object_or_404(DiaFestivo, pk=pk)
    if request.method == "POST":
        anio = festivo.fecha.year
        festivo.delete()
        messages.success(request, "Festivo eliminado.")
        return redirect(f"{_url_festivos()}?anio={anio}")
    return render(request, "reservas/festivo_eliminar.html", {"festivo": festivo, "festivo_texto": f"{festivo.fecha:%d-%m-%Y} ({festivo.descripcion})"})


def _url_festivos():
    from django.urls import reverse
    return reverse("reservas:festivos")
