from django.urls import path

from . import views

app_name = "abastecimiento"

urlpatterns = [
    path("proveedores/", views.proveedores, name="proveedores"),
    path("proveedores/nuevo/", views.proveedor_nuevo, name="proveedor_nuevo"),
    path("proveedores/<int:pk>/", views.proveedor, name="proveedor"),
    path("proveedores/<int:pk>/editar/", views.proveedor_editar, name="proveedor_editar"),
    path("ordenes/", views.ordenes, name="ordenes"),
    path("ordenes/nueva/", views.orden_nueva, name="orden_nueva"),
    path("ordenes/<int:numero>/", views.orden, name="orden"),
    path("ordenes/<int:numero>/recepcionar/", views.recepcionar, name="recepcionar"),
    path("ordenes/<int:numero>/modificar/", views.orden_modificar, name="orden_modificar"),
    path("ordenes/<int:numero>/eliminar/", views.orden_eliminar, name="orden_eliminar"),
    path("recepciones/", views.recepciones, name="recepciones"),
    path("recepciones/nueva/", views.recepcion_nueva, name="recepcion_nueva"),
]
