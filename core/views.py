from importlib import import_module

from django import forms
from django.apps import apps
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.decorators import login_not_required
from django.core.paginator import Paginator
from django.shortcuts import render

from .forms import CampoFecha, Formulario
from .models import RegistroAuditoria, SeccionAyuda
from .permisos import modulos_visibles, requiere_modulo


class FiltroAuditoriaForm(Formulario):
    operacion = forms.ChoiceField(label="Operación", required=False,
                                  choices=[("", "Todas")] + RegistroAuditoria.OPERACIONES)
    entidad = forms.CharField(label="Entidad", required=False)
    desde = CampoFecha(label="Desde", required=False)
    hasta = CampoFecha(label="Hasta", required=False)


@login_not_required
def ayuda(request):
    """HU03 · RF04 · Manual (público), solo con las secciones de los módulos del perfil.

    Sin sesión se muestra lo que puede hacer un futuro cliente: la sección general y la de reservas.
    """
    if request.user.is_authenticated:
        modulos = modulos_visibles(request.user)
    else:
        modulos = {"reserva_web"}
    secciones = SeccionAyuda.objects.filter(modulo__in={SeccionAyuda.GENERAL} | set(modulos))
    return render(request, "core/ayuda.html", {"secciones": secciones})


@login_not_required
def inicio(request):
    """Página pública con "Reservar hora" e "Ingresar" (MAQUETA-SPEC 5.4) y los servicios del catálogo."""
    servicios = apps.get_model("catalogo", "Servicio").objects.reservables().order_by("precio")
    config = settings.SERVIEXPRESS
    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    atencion = config["DIAS_ATENCION"]
    horario = {
        "dias": f"{dias[atencion[0]].capitalize()} a {dias[atencion[-1]]}" if atencion else "",
        "horas": f"{config['HORA_INICIO']:02d}:00 a {config['HORA_FIN']:02d}:00",
    }
    pasos = [
        ("Elija el servicio", "Con su precio a la vista, antes de confirmar."),
        ("Elija fecha y hora", "Solo aparecen las horas libres del taller."),
        ("Confirme", "Puede cambiar o anular su hora cuando lo necesite."),
    ]
    return render(request, "core/inicio.html", {"servicios": servicios, "horario": horario, "pasos": pasos})


def panel(request):
    """Inicio después de ingresar: indicadores, agenda y accesos directos según el perfil.

    Los datos los arma informes.tablero (la app que puede leer de todas); core no la importa directamente.
    """
    contexto = import_module("informes.tablero").contexto(request.user)
    hora = timezone.localtime().hour
    contexto["saludo"] = "Buenos días" if hora < 12 else "Buenas tardes" if hora < 20 else "Buenas noches"
    return render(request, "core/panel.html", contexto)


@requiere_modulo("auditoria")
def auditoria(request):
    """HU02 · RNF06, RNF08 · Lista del log (solo lectura), filtrable por operación y fecha."""
    form = FiltroAuditoriaForm(request.GET or None)
    registros = RegistroAuditoria.objects.select_related("usuario")
    if form.is_valid():
        datos = form.cleaned_data
        if datos["operacion"]:
            registros = registros.filter(operacion=datos["operacion"])
        if datos["entidad"]:
            registros = registros.filter(entidad__icontains=datos["entidad"])
        if datos["desde"]:
            registros = registros.filter(fecha_hora__date__gte=datos["desde"])
        if datos["hasta"]:
            registros = registros.filter(fecha_hora__date__lte=datos["hasta"])
    pagina = Paginator(registros, 50).get_page(request.GET.get("page"))
    return render(request, "core/auditoria.html", {"form": form, "page_obj": pagina})
