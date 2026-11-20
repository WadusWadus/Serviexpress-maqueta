from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),  # solo para depurar: ninguna HU se demuestra aquí
    path("", include("core.urls")),
    path("cuentas/", include("cuentas.urls")),
    path("personal/", include("personal.urls")),
    path("clientes/", include("clientes.urls")),
    path("reservas/", include("reservas.urls")),
    path("agenda/", include("reservas.urls_agenda")),
    path("atencion/", include("reservas.urls_atencion")),
    path("ventas/", include("ventas.urls")),
    path("abastecimiento/", include("abastecimiento.urls")),
    path("informes/", include("informes.urls")),
    path("catalogo/", include("catalogo.urls")),
]
