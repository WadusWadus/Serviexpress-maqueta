"""HU11 · Registrar servicio realizado · RF14 · CU06 (/atencion/)."""

from django import forms
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from catalogo.models import Servicio
from clientes.models import Cliente
from core.forms import CampoFecha, Formulario
from core.permisos import denegar, requiere_modulo
from core.validadores import normalizar_rut
from personal.servicios import empleado_de

from .models import Reserva, ServicioRealizado

MENSAJE_DERIVAR = "Cliente no registrado: derivar al Empleado Administrativo."


class RegistroConReservaForm(Formulario):
    observacion = forms.CharField(label="Observación", required=False, widget=forms.Textarea(attrs={"rows": 3}))


class RegistroSinReservaForm(Formulario):
    """Flujo 1a: el cliente llegó sin reserva."""

    rut = forms.CharField(label="RUT del cliente", max_length=12)
    servicio = forms.ModelChoiceField(label="Servicio", queryset=Servicio.objects.filter(activo=True))
    observacion = forms.CharField(label="Observación", required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def clean_rut(self):
        cliente = Cliente.objects.filter(rut=normalizar_rut(self.cleaned_data["rut"])).first()
        if cliente is None:
            raise forms.ValidationError(MENSAJE_DERIVAR)  # flujo 1b: no se crea la ficha desde aquí
        self.cliente = cliente
        return cliente.rut


def _mecanico(request):
    """El empleado se toma del usuario conectado y debe tener la función «ejecuta servicios» (C07)."""
    empleado = empleado_de(request.user)
    return empleado if empleado and empleado.ejecuta_servicios else None


def _denegar_sin_funcion(request):
    return denegar(request, "atencion",
                   "Su cuenta no está asociada a un empleado con la función «ejecuta servicios».")


@requiere_modulo("atencion")
def inicio(request):
    """HU11 · Reservas vigentes de hoy, con botón «Registrar servicio»."""
    hoy = timezone.localdate()
    reservas = Reserva.objects.filter(fecha=hoy, estado=Reserva.VIGENTE).select_related("cliente", "servicio")
    return render(request, "reservas/atencion_inicio.html", {"reservas": reservas, "hoy": hoy})


@requiere_modulo("atencion")
def registrar(request):
    """HU11 · RF14 · CU06 · Con reserva (?reserva=N) o sin reserva (flujo 1a)."""
    empleado = _mecanico(request)
    if empleado is None:
        return _denegar_sin_funcion(request)

    numero = request.GET.get("reserva")
    reserva = None
    if numero:
        reserva = Reserva.objects.filter(pk=numero, estado=Reserva.VIGENTE).select_related("cliente", "servicio").first()
        if reserva is None:
            messages.error(request, f"La reserva N° {numero} no existe o ya fue atendida o anulada.")
            return redirect("atencion:inicio")
        form = RegistroConReservaForm(request.POST or None)
    else:
        form = RegistroSinReservaForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            with transaction.atomic():
                if reserva:
                    cliente, servicio = reserva.cliente, reserva.servicio
                    reserva.estado = Reserva.ATENDIDA
                    reserva.save(update_fields=["estado"])
                else:
                    cliente, servicio = form.cliente, form.cleaned_data["servicio"]
                realizado = ServicioRealizado.objects.create(
                    cliente=cliente, servicio=servicio, reserva=reserva, empleado=empleado,
                    observacion=form.cleaned_data["observacion"],
                )
            messages.success(request, f"Servicio registrado: {realizado}. Queda pendiente de boleta o factura.")
            return redirect("atencion:realizados")
        if "rut" in form.errors and MENSAJE_DERIVAR in form.errors["rut"]:
            messages.warning(request, MENSAJE_DERIVAR)
    return render(request, "reservas/atencion_registrar.html", {"form": form, "reserva": reserva, "empleado": empleado})


class FiltroFechaForm(Formulario):
    fecha = CampoFecha(label="Fecha", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha"].widget.attrs["aria-label"] = "Fecha"


@requiere_modulo("atencion")
def realizados(request):
    """HU11 · Servicios realizados del día."""
    form = FiltroFechaForm(request.GET or None)
    fecha = form.cleaned_data["fecha"] if form.is_valid() and form.cleaned_data["fecha"] else timezone.localdate()
    lista = ServicioRealizado.objects.filter(fecha=fecha).select_related("cliente", "servicio", "empleado", "reserva")
    pagina = Paginator(lista, 50).get_page(request.GET.get("page"))
    return render(request, "reservas/atencion_realizados.html", {"page_obj": pagina, "fecha": fecha, "form": form})
