from django.urls import path

from . import views

app_name = "informes"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("estadisticas-web/", views.estadisticas_web, name="estadisticas_web"),
    path("<slug:tipo>/", views.informe, name="informe"),
]
