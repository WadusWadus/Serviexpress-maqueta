"""Área 3 · Lógica de reservas (sin vistas). HU08, HU09, HU10."""

from datetime import datetime, time, timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import DiaFestivo, Reserva


class ReservaNoDisponible(Exception):
    """La fecha u hora no se puede reservar (flujo 4a de CU04)."""


class HoraTomada(ReservaNoDisponible):
    """La hora fue tomada por otra persona entre la elección y la confirmación (flujo 5a)."""


MENSAJE_HORA_TOMADA = "La hora elegida acaba de ser reservada por otra persona. Elija otra."


def es_festivo(fecha):
    """HU09 · RF12 · La usa la reserva (HU08) para no ofrecer los festivos."""
    return DiaFestivo.objects.filter(fecha=fecha).exists()


def _cfg(clave):
    return settings.SERVIEXPRESS[clave]


def bloques_del_dia():
    """Horas de inicio de los bloques del horario (valores DEMO, pendiente V07)."""
    bloques, actual = [], datetime.combine(datetime.today(), time(_cfg("HORA_INICIO")))
    fin = datetime.combine(datetime.today(), time(_cfg("HORA_FIN")))
    while actual + timedelta(minutes=_cfg("DURACION_BLOQUE_MIN")) <= fin:
        bloques.append(actual.time())
        actual += timedelta(minutes=_cfg("DURACION_BLOQUE_MIN"))
    return bloques


def motivo_fecha_no_disponible(fecha):
    """None si la fecha se puede reservar; si no, el mensaje para el usuario."""
    hoy = timezone.localdate()
    if fecha < hoy:
        return "Fecha no disponible: ya pasó."
    if fecha > hoy + timedelta(days=_cfg("DIAS_ADELANTE_RESERVA")):
        return f"Fecha no disponible: se reserva con hasta {_cfg('DIAS_ADELANTE_RESERVA')} días de anticipación."
    if fecha.weekday() not in _cfg("DIAS_ATENCION"):
        return "Fecha no disponible: el taller no atiende ese día."
    if es_festivo(fecha):
        return "Fecha no disponible: día festivo."
    return None


def horas_disponibles(fecha, excluir=None):
    """Bloques libres de la fecha. Vacío si es festiva, no es día de atención o ya pasó."""
    if motivo_fecha_no_disponible(fecha):
        return []
    ocupadas = Reserva.objects.filter(fecha=fecha, estado=Reserva.VIGENTE)
    if excluir is not None:
        ocupadas = ocupadas.exclude(pk=excluir.pk)
    ocupadas = set(ocupadas.values_list("hora_inicio", flat=True))
    libres = [b for b in bloques_del_dia() if b not in ocupadas]
    if fecha == timezone.localdate():
        ahora = timezone.localtime().time()
        libres = [b for b in libres if b > ahora]
    return libres


def fechas_ofrecidas(excluir=None):
    """Fechas de los próximos días con al menos una hora libre (los festivos no se ofrecen)."""
    hoy = timezone.localdate()
    fechas = (hoy + timedelta(days=i) for i in range(_cfg("DIAS_ADELANTE_RESERVA") + 1))
    return [f for f in fechas if horas_disponibles(f, excluir)]


def _validar(fecha, hora, excluir=None):
    motivo = motivo_fecha_no_disponible(fecha)
    if motivo:
        raise ReservaNoDisponible(motivo)
    if hora not in bloques_del_dia():
        raise ReservaNoDisponible("Hora no disponible: no corresponde a un bloque del horario de atención.")
    if hora not in horas_disponibles(fecha, excluir):
        raise HoraTomada(MENSAJE_HORA_TOMADA)


def crear_reserva(cliente, servicio, fecha, hora, usuario, canal):
    """HU08 · RF10, RF11 · Valida en el servidor y crea la reserva."""
    if not servicio.activo:
        raise ReservaNoDisponible("El servicio elegido ya no está disponible para reservar.")
    _validar(fecha, hora)
    try:
        with transaction.atomic():
            return Reserva.objects.create(cliente=cliente, servicio=servicio, fecha=fecha, hora_inicio=hora,
                                          canal=canal, creada_por=usuario)
    except IntegrityError:
        raise HoraTomada(MENSAJE_HORA_TOMADA)


def cambiar_reserva(reserva, fecha, hora):
    """HU10 · RF13 · Mueve la reserva: la hora anterior queda libre."""
    if not reserva.modificable:
        raise ReservaNoDisponible("Solo se pueden cambiar reservas vigentes con fecha futura.")
    _validar(fecha, hora, excluir=reserva)
    reserva.fecha, reserva.hora_inicio = fecha, hora
    try:
        with transaction.atomic():
            reserva.save(update_fields=["fecha", "hora_inicio"])
    except IntegrityError:
        raise HoraTomada(MENSAJE_HORA_TOMADA)
    return reserva


def anular_reserva(reserva):
    """HU10 · RF13 · La anulación libera la hora."""
    if not reserva.modificable:
        raise ReservaNoDisponible("Solo se pueden anular reservas vigentes con fecha futura.")
    reserva.estado = Reserva.ANULADA
    reserva.save(update_fields=["estado"])
    return reserva
