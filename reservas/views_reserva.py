"""HU08, HU10 · Reservar, cambiar y anular horas · RF10, RF11, RF13 · RNF18, RNF19 · CU04.

El mismo flujo de 3 pantallas sirve para dos canales:
- WEB:   el Cliente reserva para sí mismo (/reservas/nueva/ …), módulo reserva_web.
- LOCAL: el Empleado Administrativo reserva para un cliente (/agenda/nueva/ …), módulo agenda,
         con un paso previo para buscar al cliente por RUT.
El avance se guarda en la sesión (clave `reserva_en_curso`).
"""

from datetime import date, time

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from catalogo.models import Servicio
from clientes.models import Cliente
from clientes.views import buscar_clientes
from core.permisos import requiere_modulo

from . import servicios as srv
from .models import Reserva

CLAVE = "reserva_en_curso"
WEB = {"canal": Reserva.WEB, "ns": "reservas", "volver": "reservas:mis_reservas", "pasos": 3}
LOCAL = {"canal": Reserva.LOCAL, "ns": "agenda", "volver": "agenda:lista", "pasos": 4}


# ---------------------------------------------------------------- utilidades del flujo

def _en_curso(request):
    return request.session.get(CLAVE, {})


def _guardar(request, **datos):
    actual = _en_curso(request)
    actual.update(datos)
    request.session[CLAVE] = actual


def _url(modo, nombre, **kwargs):
    return reverse(f"{modo['ns']}:{nombre}", kwargs=kwargs or None)


def _cliente(request, modo):
    """Cliente para el que se reserva, o None."""
    if modo is WEB:
        return Cliente.objects.filter(usuario=request.user).first()
    cliente_id = _en_curso(request).get("cliente_id")
    return Cliente.objects.filter(pk=cliente_id).first() if cliente_id else None


def _sin_cliente(request, modo):
    if modo is WEB:
        messages.error(request, "Su cuenta no tiene ficha de cliente. Para reservar en el local use la Agenda.")
        return redirect("core:panel")
    messages.info(request, "Primero busque al cliente.")
    return redirect("agenda:nueva")


def _parse_fecha(texto):
    try:
        return date.fromisoformat(texto)
    except (TypeError, ValueError):
        return None


def _parse_hora(texto):
    try:
        return time.fromisoformat(texto)
    except (TypeError, ValueError):
        return None


def _reserva_a_cambiar(request):
    numero = _en_curso(request).get("cambiar")
    return Reserva.objects.filter(pk=numero).first() if numero else None


def _contexto(modo, paso, **extra):
    return {"modo": modo, "ns": modo["ns"], "paso": paso, "total_pasos": modo["pasos"],
            "es_local": modo is LOCAL, **extra}


# ---------------------------------------------------------------- pantalla 1: servicio

def _paso_servicio(request, modo):
    cliente = _cliente(request, modo)
    if cliente is None:
        return _sin_cliente(request, modo)
    servicios = Servicio.objects.reservables()
    if request.method == "POST":
        servicio = servicios.filter(pk=request.POST.get("servicio")).first()
        if servicio is None:
            messages.error(request, "Servicio: elija un servicio de la lista.")
        else:
            _guardar(request, servicio_id=servicio.pk, cambiar=None)
            return redirect(_url(modo, "paso_fecha"))
    elif modo is WEB:
        request.session[CLAVE] = {}  # empieza una reserva nueva
    else:
        _guardar(request, cambiar=None)
    return render(request, "reservas/paso_servicio.html", _contexto(
        modo, 1 if modo is WEB else 2, servicios=servicios, cliente=cliente,
        elegido=_en_curso(request).get("servicio_id"),
    ))


# ---------------------------------------------------------------- pantalla 2: fecha y hora

def _paso_fecha(request, modo):
    cliente = _cliente(request, modo)
    if cliente is None:
        return _sin_cliente(request, modo)
    datos = _en_curso(request)
    servicio = Servicio.objects.filter(pk=datos.get("servicio_id")).first()
    if servicio is None:
        return redirect(_url(modo, "paso_servicio"))
    cambiar = _reserva_a_cambiar(request)

    if request.method == "POST":
        fecha, hora = _parse_fecha(request.POST.get("fecha")), _parse_hora(request.POST.get("hora"))
        motivo = None
        if fecha is None:
            motivo = "Fecha: elija una fecha válida."
        elif hora is None:
            motivo = "Hora: elija una hora."
        else:
            motivo = srv.motivo_fecha_no_disponible(fecha)  # validación en el servidor (flujo 4a)
            if motivo is None and hora not in srv.horas_disponibles(fecha, cambiar):
                motivo = "Hora no disponible: elija otra."
        if motivo is None:
            _guardar(request, fecha=fecha.isoformat(), hora=hora.strftime("%H:%M"))
            return redirect(_url(modo, "paso_confirmar"))
        messages.error(request, motivo)
        fecha_vista = fecha
    else:
        fecha_vista = _parse_fecha(request.GET.get("fecha") or datos.get("fecha"))

    fechas = srv.fechas_ofrecidas(cambiar)
    if fecha_vista is None:
        fecha_vista = fechas[0] if fechas else None
    motivo_vista = srv.motivo_fecha_no_disponible(fecha_vista) if fecha_vista else None
    if motivo_vista and request.method == "GET":
        messages.error(request, motivo_vista)
    horas = srv.horas_disponibles(fecha_vista, cambiar) if fecha_vista else []
    return render(request, "reservas/paso_fecha.html", _contexto(
        modo, 2 if modo is WEB else 3, servicio=servicio, cliente=cliente, fechas=fechas,
        fecha_vista=fecha_vista, horas=horas, cambiar=cambiar,
    ))


# ---------------------------------------------------------------- pantalla 3: confirmar

def _paso_confirmar(request, modo):
    cliente = _cliente(request, modo)
    if cliente is None:
        return _sin_cliente(request, modo)
    datos = _en_curso(request)
    servicio = Servicio.objects.filter(pk=datos.get("servicio_id")).first()
    fecha, hora = _parse_fecha(datos.get("fecha")), _parse_hora(datos.get("hora"))
    if servicio is None or fecha is None or hora is None:
        return redirect(_url(modo, "paso_servicio"))
    cambiar = _reserva_a_cambiar(request)

    if request.method == "POST":
        try:
            if cambiar:
                reserva = srv.cambiar_reserva(cambiar, fecha, hora)
                mensaje = f"Reserva N° {reserva.numero} cambiada al {fecha:%d-%m-%Y} a las {hora:%H:%M}."
            else:
                reserva = srv.crear_reserva(cliente, servicio, fecha, hora, request.user, modo["canal"])
                mensaje = f"Reserva N° {reserva.numero} registrada."
        except srv.ReservaNoDisponible as error:
            messages.error(request, str(error))  # flujo 5a: vuelve a la pantalla 2
            return redirect(f"{_url(modo, 'paso_fecha')}?fecha={fecha.isoformat()}")
        request.session[CLAVE] = {}
        messages.success(request, mensaje)
        return redirect(modo["volver"])
    return render(request, "reservas/paso_confirmar.html", _contexto(
        modo, 3 if modo is WEB else 4, servicio=servicio, cliente=cliente, fecha=fecha, hora=hora, cambiar=cambiar,
    ))


# ---------------------------------------------------------------- canal web (Cliente)

@requiere_modulo("reserva_web")
def nueva(request):
    """HU08 · Pantalla 1 de 3."""
    return _paso_servicio(request, WEB)


@requiere_modulo("reserva_web")
def nueva_fecha(request):
    """HU08 · Pantalla 2 de 3."""
    return _paso_fecha(request, WEB)


@requiere_modulo("reserva_web")
def nueva_confirmar(request):
    """HU08 · Pantalla 3 de 3."""
    return _paso_confirmar(request, WEB)


@requiere_modulo("reserva_web")
def mis_reservas(request):
    """HU10 · RF13 · Reservas vigentes y pasadas del cliente."""
    cliente = _cliente(request, WEB)
    if cliente is None:
        return _sin_cliente(request, WEB)
    reservas = cliente.reservas.select_related("servicio").order_by("-fecha", "-hora_inicio")
    proximas = [r for r in reservas if r.modificable]
    historial = [r for r in reservas if not r.modificable]
    return render(request, "reservas/mis_reservas.html", {"proximas": proximas, "historial": historial})


def _reserva_del_cliente(request, numero):
    """Un cliente solo ve y toca sus reservas: otro número → 404."""
    cliente = _cliente(request, WEB)
    if cliente is None:
        raise Http404
    return get_object_or_404(Reserva, pk=numero, cliente=cliente)


def _iniciar_cambio(request, reserva, modo):
    if not reserva.modificable:
        messages.error(request, "Solo se pueden cambiar reservas vigentes con fecha futura.")
        return redirect(modo["volver"])
    request.session[CLAVE] = {"servicio_id": reserva.servicio_id, "cambiar": reserva.pk, "cliente_id": reserva.cliente_id,
                              "fecha": reserva.fecha.isoformat()}
    return redirect(_url(modo, "paso_fecha"))


def _anular(request, reserva, modo):
    if request.method == "POST":
        try:
            srv.anular_reserva(reserva)
            messages.success(request, f"Reserva N° {reserva.numero} anulada. La hora quedó libre.")
        except srv.ReservaNoDisponible as error:
            messages.error(request, str(error))
        return redirect(modo["volver"])
    if not reserva.modificable:
        messages.error(request, "Solo se pueden anular reservas vigentes con fecha futura.")
        return redirect(modo["volver"])
    return render(request, "reservas/anular.html", {"reserva": reserva, "volver": modo["volver"]})


@requiere_modulo("reserva_web")
def cambiar(request, numero):
    """HU10 · RF13 · Reutiliza las pantallas 2 y 3 de HU08."""
    return _iniciar_cambio(request, _reserva_del_cliente(request, numero), WEB)


@requiere_modulo("reserva_web")
def anular(request, numero):
    """HU10 · RF13"""
    return _anular(request, _reserva_del_cliente(request, numero), WEB)


# ---------------------------------------------------------------- canal local (Agenda)

@requiere_modulo("agenda")
def agenda(request):
    """HU08 · RF10 · Reservas del día y de los próximos días."""
    hoy = timezone.localdate()
    fecha = _parse_fecha(request.GET.get("fecha"))
    reservas = Reserva.objects.select_related("cliente", "servicio")
    if fecha:
        reservas = reservas.filter(fecha=fecha)
    else:
        reservas = reservas.filter(fecha__gte=hoy, estado=Reserva.VIGENTE)
    pagina = Paginator(reservas, 50).get_page(request.GET.get("page"))
    return render(request, "reservas/agenda.html", {"page_obj": pagina, "fecha": fecha, "hoy": hoy})


@requiere_modulo("agenda")
def agenda_nueva(request):
    """HU08 · RF10 · Paso previo del canal local: buscar al cliente por RUT o nombre."""
    if request.method == "POST":
        cliente = Cliente.objects.filter(pk=request.POST.get("cliente")).first()
        if cliente:
            request.session[CLAVE] = {"cliente_id": cliente.pk}
            return redirect("agenda:paso_servicio")
        messages.error(request, "Cliente: elija un cliente de la lista.")
    q = request.GET.get("q", "").strip()
    resultados = buscar_clientes(q)[:20] if q else []
    return render(request, "reservas/agenda_buscar_cliente.html", _contexto(LOCAL, 1, q=q, resultados=resultados))


@requiere_modulo("agenda")
def agenda_servicio(request):
    return _paso_servicio(request, LOCAL)


@requiere_modulo("agenda")
def agenda_fecha(request):
    return _paso_fecha(request, LOCAL)


@requiere_modulo("agenda")
def agenda_confirmar(request):
    return _paso_confirmar(request, LOCAL)


@requiere_modulo("agenda")
def agenda_cambiar(request, numero):
    """HU10 · El Empleado Administrativo cambia una reserva desde la agenda."""
    return _iniciar_cambio(request, get_object_or_404(Reserva, pk=numero), LOCAL)


@requiere_modulo("agenda")
def agenda_anular(request, numero):
    return _anular(request, get_object_or_404(Reserva, pk=numero), LOCAL)
