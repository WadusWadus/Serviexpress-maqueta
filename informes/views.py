"""Área 7 · Informes y gestión. HU22 · RF30, RF31 · RNF03 · CU15."""

from django.http import Http404
from django.shortcuts import render

from core.permisos import requiere_modulo

from . import consultas, estadisticas, exportar
from .forms import InformeForm


@requiere_modulo("estadisticas_web")
def estadisticas_web(request):
    """HU24 · RF33 · CU16 · Visitas por día, semana y mes, con tabla y gráfico."""
    series = [
        ("dia", "Por día (últimos 30)", estadisticas.por_dia()),
        ("semana", "Por semana (últimas 12)", estadisticas.por_semana()),
        ("mes", "Por mes (últimos 12)", estadisticas.por_mes()),
    ]
    graficos = {clave: {"etiquetas": [e for e, _ in datos], "valores": [v for _, v in datos]} for clave, _, datos in series}
    return render(request, "informes/estadisticas_web.html", {"series": series, "graficos": graficos})


@requiere_modulo("informes")
def inicio(request):
    """HU22 · Selector de tipo de informe."""
    return render(request, "informes/inicio.html", {"tipos": consultas.TIPOS})


def _generar(request, tipo):
    if tipo not in consultas.TIPOS:
        raise Http404
    form = InformeForm(request.GET or None, tipo=tipo)
    if not request.GET:
        form = InformeForm({"desde": consultas.rango_por_defecto()[0], "hasta": consultas.rango_por_defecto()[1]}, tipo=tipo)
    informe = None
    if form.is_valid():
        datos = form.cleaned_data
        informe = consultas.generar(tipo, datos["desde"], datos["hasta"], **{
            k: datos.get(k) for k in ("cliente", "servicio", "empleado", "proveedor")})
    return form, informe


@requiere_modulo("informes")
def informe(request, tipo):
    """HU22 · RF30, RF31 · Vista previa; ?imprimir=1 da la versión limpia y ?formato= exporta (HU23)."""
    form, resultado = _generar(request, tipo)
    contexto = {"form": form, "informe": resultado, "tipo": tipo, "titulo": consultas.TIPOS[tipo]["titulo"]}
    formato = request.GET.get("formato")
    if formato in exportar.EXPORTADORES and resultado:
        return exportar.exportar(resultado, formato)  # HU23 · RF32
    if request.GET.get("imprimir") == "1" and resultado:
        return render(request, "informes/imprimir.html", contexto)
    return render(request, "informes/informe.html", contexto)
