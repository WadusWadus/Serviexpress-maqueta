"""HU24 · Estadísticas de visitas web · RF33 · CU16"""

from datetime import datetime, time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.tests.fabricas import crear_usuario
from informes import estadisticas
from informes.models import VisitaWeb


class EstadisticasWebTests(TestCase):
    def setUp(self):
        self.hoy = timezone.localdate()

    def visita(self, dias_atras, clave="s", ruta="/"):
        momento = timezone.make_aware(datetime.combine(self.hoy - timedelta(days=dias_atras), time(12)))
        return VisitaWeb.objects.create(fecha_hora=momento, ruta=ruta, clave_sesion=clave)

    def test_visitas_por_dia(self):
        self.visita(0, "a")
        self.visita(0, "b")
        self.visita(1, "c")
        dias = estadisticas.por_dia()
        self.assertEqual(len(dias), 30)
        self.assertEqual(dias[-1], (f"{self.hoy:%d-%m}", 2))
        self.assertEqual(dias[-2][1], 1)

    def test_visitas_por_semana(self):
        self.visita(0, "a")
        self.visita(7, "b")
        self.visita(7, "c")
        semanas = estadisticas.por_semana()
        self.assertEqual(len(semanas), 12)
        self.assertEqual(semanas[-1][1], 1)  # hoy cae en la semana actual; hace 7 días, en la anterior
        self.assertEqual(semanas[-2][1], 2)
        self.assertEqual(sum(v for _, v in semanas), 3)

    def test_visitas_por_mes(self):
        self.visita(0, "a")
        self.visita(40, "b")
        meses = estadisticas.por_mes()
        self.assertEqual(len(meses), 12)
        self.assertEqual(sum(v for _, v in meses), 2)
        self.assertGreaterEqual(meses[-1][1], 1)

    def test_middleware_registra_visita_publica(self):
        self.client.get(reverse("core:inicio"))
        self.client.get(reverse("cuentas:ingresar"))
        self.assertEqual(sorted(VisitaWeb.objects.values_list("ruta", flat=True)), ["/", "/cuentas/ingresar/"])
        admin = crear_usuario("admin", "ADMIN")
        self.client.force_login(admin)
        self.client.get(reverse("cuentas:usuarios"))  # pantalla interna: no cuenta
        self.client.get(reverse("reservas:festivos"))  # interna aunque esté bajo /reservas/
        self.assertEqual(VisitaWeb.objects.count(), 2)

    def test_middleware_no_cuenta_recargas(self):
        for _ in range(3):
            self.client.get(reverse("core:inicio"))
        self.assertEqual(VisitaWeb.objects.count(), 1)

    def test_estadisticas_solo_admin(self):
        self.client.force_login(crear_usuario("administrativo", "ADMINISTRATIVO"))
        self.assertEqual(self.client.get(reverse("informes:estadisticas_web")).status_code, 403)
        self.client.force_login(crear_usuario("admin", "ADMIN"))
        respuesta = self.client.get(reverse("informes:estadisticas_web"))
        self.assertContains(respuesta, "Por día (últimos 30)")
        self.assertContains(respuesta, "chart.js@4.4.1")
