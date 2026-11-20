from django.urls import path

from . import views

app_name = "clientes"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nuevo/", views.nuevo, name="nuevo"),
    path("<int:pk>/", views.ficha, name="ficha"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("fiado/", views.fiado, name="fiado"),
    path("<int:pk>/fiado/", views.fiado_cambiar, name="fiado_cambiar"),
    path("<int:pk>/saldo/", views.saldo, name="saldo"),
]
