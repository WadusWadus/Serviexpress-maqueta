from django.urls import path

from . import views

app_name = "cuentas"

urlpatterns = [
    path("ingresar/", views.ingresar, name="ingresar"),
    path("salir/", views.salir, name="salir"),
    path("usuarios/", views.lista_usuarios, name="usuarios"),
    path("usuarios/nuevo/", views.nuevo_usuario, name="nuevo_usuario"),
    path("usuarios/<int:pk>/editar/", views.editar_usuario, name="editar_usuario"),
    path("usuarios/<int:pk>/desactivar/", views.desactivar_usuario, name="desactivar_usuario"),
]
