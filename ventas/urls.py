from django.urls import path

from . import views

app_name = "ventas"

urlpatterns = [
    path("boletas/", views.boletas, name="boletas"),
    path("boletas/nueva/", views.boleta_nueva, name="boleta_nueva"),
    path("boletas/<int:numero>/", views.boleta, name="boleta"),
    path("boletas/<int:numero>/modificar/", views.boleta_modificar, name="boleta_modificar"),
    path("boletas/<int:numero>/anular/", views.boleta_anular, name="boleta_anular"),
    path("facturas/", views.facturas, name="facturas"),
    path("facturas/nueva/", views.factura_nueva, name="factura_nueva"),
    path("facturas/<int:numero>/", views.factura, name="factura"),
]
