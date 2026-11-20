"""HU08, HU10 · Canal local de reservas (/agenda/)."""

from django.urls import path

from . import views_reserva as v

app_name = "agenda"

urlpatterns = [
    path("", v.agenda, name="lista"),
    path("nueva/", v.agenda_nueva, name="nueva"),
    path("nueva/servicio/", v.agenda_servicio, name="paso_servicio"),
    path("nueva/fecha/", v.agenda_fecha, name="paso_fecha"),
    path("nueva/confirmar/", v.agenda_confirmar, name="paso_confirmar"),
    path("<int:numero>/cambiar/", v.agenda_cambiar, name="cambiar"),
    path("<int:numero>/anular/", v.agenda_anular, name="anular"),
]
