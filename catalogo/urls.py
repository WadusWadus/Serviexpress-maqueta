from django.urls import path

from . import views

app_name = "catalogo"

urlpatterns = [
    path("productos/", views.productos, name="productos"),
    path("productos/nuevo/", views.producto_nuevo, name="producto_nuevo"),
    path("productos/<int:pk>/editar/", views.producto_editar, name="producto_editar"),
    path("productos/<int:pk>/desactivar/", views.producto_desactivar, name="producto_desactivar"),
    path("servicios/", views.servicios, name="servicios"),
    path("servicios/nuevo/", views.servicio_nuevo, name="servicio_nuevo"),
    path("servicios/<int:pk>/", views.servicio_detalle, name="servicio_detalle"),
    path("servicios/<int:pk>/editar/", views.servicio_editar, name="servicio_editar"),
    path("servicios/<int:pk>/desactivar/", views.servicio_desactivar, name="servicio_desactivar"),
]
