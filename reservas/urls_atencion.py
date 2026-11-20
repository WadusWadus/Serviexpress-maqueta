"""HU11 · Atención en el taller (/atencion/)."""

from django.urls import path

from . import views_atencion as v

app_name = "atencion"

urlpatterns = [
    path("", v.inicio, name="inicio"),
    path("registrar/", v.registrar, name="registrar"),
    path("realizados/", v.realizados, name="realizados"),
]
