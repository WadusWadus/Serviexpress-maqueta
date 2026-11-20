from django.urls import path

from . import views

app_name = "personal"

urlpatterns = [
    path("empleados/", views.lista, name="lista"),
    path("empleados/nuevo/", views.nuevo, name="nuevo"),
    path("empleados/<int:pk>/editar/", views.editar, name="editar"),
]
