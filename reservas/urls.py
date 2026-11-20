from django.urls import path

from . import views, views_reserva

app_name = "reservas"

urlpatterns = [
    # HU08 · Reserva web en 3 pantallas
    path("nueva/", views_reserva.nueva, name="paso_servicio"),
    path("nueva/fecha/", views_reserva.nueva_fecha, name="paso_fecha"),
    path("nueva/confirmar/", views_reserva.nueva_confirmar, name="paso_confirmar"),
    # HU10 · Cambiar o anular
    path("mis-reservas/", views_reserva.mis_reservas, name="mis_reservas"),
    path("<int:numero>/cambiar/", views_reserva.cambiar, name="cambiar"),
    path("<int:numero>/anular/", views_reserva.anular, name="anular"),
    # HU09 · Días festivos
    path("festivos/", views.festivos, name="festivos"),
    path("festivos/nuevo/", views.festivo_nuevo, name="festivo_nuevo"),
    path("festivos/<int:pk>/editar/", views.festivo_editar, name="festivo_editar"),
    path("festivos/<int:pk>/eliminar/", views.festivo_eliminar, name="festivo_eliminar"),
]
