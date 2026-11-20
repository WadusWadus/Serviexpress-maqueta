"""HU24 · RF33 · CU16 · Visitas por día (30), por semana (12) y por mes (12)."""

from collections import Counter
from datetime import timedelta

from django.utils import timezone

from .models import VisitaWeb

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def _fechas_locales(desde):
    inicio = timezone.make_aware(timezone.datetime.combine(desde, timezone.datetime.min.time()))
    return [timezone.localtime(f).date() for f in VisitaWeb.objects.filter(fecha_hora__gte=inicio).values_list("fecha_hora", flat=True)]


def por_dia(dias=30):
    hoy = timezone.localdate()
    desde = hoy - timedelta(days=dias - 1)
    conteo = Counter(_fechas_locales(desde))
    return [(f"{d:%d-%m}", conteo.get(d, 0)) for d in (desde + timedelta(days=i) for i in range(dias))]


def por_semana(semanas=12):
    hoy = timezone.localdate()
    lunes_actual = hoy - timedelta(days=hoy.weekday())
    desde = lunes_actual - timedelta(weeks=semanas - 1)
    conteo = Counter(f - timedelta(days=f.weekday()) for f in _fechas_locales(desde))
    lunes = [desde + timedelta(weeks=i) for i in range(semanas)]
    return [(f"Sem. {l:%d-%m}", conteo.get(l, 0)) for l in lunes]


def por_mes(meses=12):
    hoy = timezone.localdate()
    pares = []
    anio, mes = hoy.year, hoy.month
    for _ in range(meses):
        pares.append((anio, mes))
        anio, mes = (anio, mes - 1) if mes > 1 else (anio - 1, 12)
    pares.reverse()
    desde = timezone.datetime(pares[0][0], pares[0][1], 1).date()
    conteo = Counter((f.year, f.month) for f in _fechas_locales(desde))
    return [(f"{MESES[m - 1]} {a}", conteo.get((a, m), 0)) for a, m in pares]
