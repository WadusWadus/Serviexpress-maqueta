"""Datos demo de reservas y atención."""

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from catalogo.models import Servicio
from clientes.models import Cliente

from .models import DiaFestivo, Reserva
from .servicios import horas_disponibles

# Solo los feriados irrenunciables confirmados de 2026 y 2027, según el archivo
# feriados_irrenunciables_chile_2026_2027.csv entregado por el equipo. Decisión del equipo:
# los demás feriados (Semana Santa, San Pedro y San Pablo, etc.) no se cargan en la maqueta;
# el Administrador puede agregarlos desde /reservas/festivos/ (HU09). La pantalla de festivos
# y la de reserva lo avisan (parciales/aviso_feriados.html).
FERIADOS_IRRENUNCIABLES = [
    (date(2026, 1, 1), "Año Nuevo"),
    (date(2026, 5, 1), "Día Nacional del Trabajo"),
    (date(2026, 9, 18), "Independencia Nacional"),
    (date(2026, 9, 19), "Día de las Glorias del Ejército"),
    (date(2026, 12, 25), "Navidad"),
    (date(2027, 1, 1), "Año Nuevo"),
    (date(2027, 5, 1), "Día Nacional del Trabajo"),
    (date(2027, 9, 18), "Independencia Nacional"),
    (date(2027, 9, 19), "Día de las Glorias del Ejército"),
    (date(2027, 12, 25), "Navidad"),
]


def cargar(salida):
    for fecha, descripcion in FERIADOS_IRRENUNCIABLES:
        DiaFestivo.objects.get_or_create(fecha=fecha, defaults={"descripcion": descripcion})
    salida.write("  reservas: 10 feriados irrenunciables de 2026 y 2027")
    _cargar_reservas(salida)
    _cargar_reserva_de_hoy(salida)


def _proximos_bloques(cantidad, desde=1):
    """Bloques libres de los próximos días hábiles (respeta festivos y horario)."""
    hoy, encontrados, dia = timezone.localdate(), [], desde
    while len(encontrados) < cantidad and dia <= 30:
        fecha = hoy + timedelta(days=dia)
        libres = horas_disponibles(fecha)
        if libres:
            encontrados.append((fecha, libres[min(1, len(libres) - 1)]))
        dia += 1
    return encontrados


def _cargar_reservas(salida):
    """S2 · 3 reservas vigentes de cliente1 en los próximos días y 1 anulada."""
    cliente = Cliente.objects.get(usuario__username="cliente1")
    if cliente.reservas.exists():
        return
    usuario = cliente.usuario
    servicios = list(Servicio.objects.reservables().order_by("nombre")[:3])
    for (fecha, hora), servicio in zip(_proximos_bloques(3), servicios):
        Reserva.objects.create(cliente=cliente, servicio=servicio, fecha=fecha, hora_inicio=hora,
                               canal=Reserva.WEB, creada_por=usuario)
    fecha, hora = _proximos_bloques(1, desde=5)[0]
    Reserva.objects.create(cliente=cliente, servicio=servicios[0], fecha=fecha, hora_inicio=hora,
                           canal=Reserva.LOCAL, estado=Reserva.ANULADA,
                           creada_por=get_user_model().objects.get(username="administrativo"))
    salida.write("  reservas: 3 vigentes y 1 anulada de cliente1")


def _cargar_reserva_de_hoy(salida):
    """S3 · Una reserva de hoy de cliente1, para mostrar HU11 en /atencion/ cualquier día que se haga la demo."""
    from datetime import time

    hoy = timezone.localdate()
    cliente = Cliente.objects.get(usuario__username="cliente1")
    if Reserva.objects.filter(cliente=cliente, fecha=hoy).exists():
        return
    ocupadas = set(Reserva.objects.filter(fecha=hoy, estado=Reserva.VIGENTE).values_list("hora_inicio", flat=True))
    hora = next((time(h) for h in range(17, 8, -1) if time(h) not in ocupadas), None)
    if hora is None:
        return
    Reserva.objects.create(cliente=cliente, servicio=Servicio.objects.get(nombre="Cambio de pastillas"), fecha=hoy,
                           hora_inicio=hora, canal=Reserva.WEB, creada_por=cliente.usuario)
    salida.write("  reservas: 1 reserva de hoy de cliente1 (demo de HU11)")
