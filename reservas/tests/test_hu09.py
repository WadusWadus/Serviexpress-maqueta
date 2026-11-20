"""HU09 · Días festivos · RF12 · CU05"""

from datetime import date

from django.test import TestCase
from django.urls import reverse

from core.tests.fabricas import crear_usuario
from reservas.models import DiaFestivo
from reservas.servicios import es_festivo


class FestivosTests(TestCase):
    def setUp(self):
        self.client.force_login(crear_usuario("admin", "ADMIN"))

    def test_es_festivo_devuelve_true_para_fecha_registrada(self):
        self.client.post(reverse("reservas:festivo_nuevo"), {"fecha": "2026-12-08", "descripcion": "Inmaculada"})
        self.assertTrue(es_festivo(date(2026, 12, 8)))
        self.assertFalse(es_festivo(date(2026, 12, 9)))

    def test_fecha_festiva_duplicada_es_rechazada(self):
        DiaFestivo.objects.create(fecha=date(2026, 12, 25), descripcion="Navidad")
        respuesta = self.client.post(reverse("reservas:festivo_nuevo"), {"fecha": "2026-12-25", "descripcion": "Otra"})
        self.assertContains(respuesta, "Esa fecha ya está registrada como festiva")
        self.assertEqual(DiaFestivo.objects.count(), 1)

    def test_lista_por_anio(self):
        DiaFestivo.objects.create(fecha=date(2026, 9, 18), descripcion="Independencia")
        DiaFestivo.objects.create(fecha=date(2027, 9, 18), descripcion="Independencia 2027")
        respuesta = self.client.get(reverse("reservas:festivos"), {"anio": 2027})
        self.assertContains(respuesta, "Independencia 2027")
        self.assertNotContains(respuesta, "18-09-2026")

    def test_solo_admin_gestiona_festivos(self):
        self.client.force_login(crear_usuario("ana", "ADMINISTRATIVO"))
        self.assertEqual(self.client.get(reverse("reservas:festivos")).status_code, 403)


class AvisoFeriadosTests(TestCase):
    """Aviso de la maqueta: solo están cargados los feriados irrenunciables (decisión del equipo)."""

    def test_demo_carga_solo_los_irrenunciables(self):
        from reservas.demo import FERIADOS_IRRENUNCIABLES
        fechas = {f for f, _ in FERIADOS_IRRENUNCIABLES}
        self.assertEqual(len(fechas), 10)
        self.assertEqual({(f.month, f.day) for f in fechas}, {(1, 1), (5, 1), (9, 18), (9, 19), (12, 25)})
        self.assertEqual({f.year for f in fechas}, {2026, 2027})

    def test_aviso_en_festivos_y_en_la_reserva(self):
        from core.tests.fabricas import crear_cliente, crear_servicio
        self.client.force_login(crear_usuario("admin", "ADMIN"))
        respuesta = self.client.get(reverse("reservas:festivos")).content.decode()
        self.assertIn("Solo están cargados los feriados irrenunciables", respuesta)
        # El aviso va en el cuerpo de la página, no dentro del <title>.
        self.assertNotIn("aviso-feriados", respuesta[:respuesta.index("</title>")])
        self.assertLess(respuesta.index("<main"), respuesta.index('id="aviso-feriados"'))
        cliente = crear_cliente("cliente1")
        self.client.force_login(cliente.usuario)
        self.client.post(reverse("reservas:paso_servicio"), {"servicio": crear_servicio().pk})
        pagina = self.client.get(reverse("reservas:paso_fecha")).content.decode()
        self.assertNotIn("aviso-feriados", pagina[:pagina.index("</title>")])
        self.assertLess(pagina.index("<main"), pagina.index('id="aviso-feriados"'))
