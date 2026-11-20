"""HU10 · Cambiar o anular la reserva · RF13 · CU04"""

from datetime import time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.tests.fabricas import crear_cliente, crear_reserva, crear_servicio, crear_usuario, proximo_dia_habil
from reservas.models import Reserva
from reservas.servicios import horas_disponibles


class CambiarAnularTests(TestCase):
    def setUp(self):
        self.cliente = crear_cliente("cliente1")
        self.servicio = crear_servicio("Cambio de aceite")
        self.fecha = proximo_dia_habil()
        self.reserva = crear_reserva(self.cliente, self.servicio, self.fecha, time(10))
        self.client.force_login(self.cliente.usuario)

    def test_cambio_libera_hora_anterior(self):
        self.assertNotIn(time(10), horas_disponibles(self.fecha))
        self.client.get(reverse("reservas:cambiar", args=[self.reserva.numero]))
        self.client.post(reverse("reservas:paso_fecha"), {"fecha": self.fecha.isoformat(), "hora": "12:00"})
        respuesta = self.client.post(reverse("reservas:paso_confirmar"), follow=True)
        self.assertContains(respuesta, f"Reserva N° {self.reserva.numero} cambiada")
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.hora_inicio, time(12))
        self.assertEqual(Reserva.objects.count(), 1)
        self.assertIn(time(10), horas_disponibles(self.fecha))
        # Otro cliente puede tomar la hora liberada.
        otro = crear_cliente("cliente2")
        self.client.force_login(otro.usuario)
        self.client.post(reverse("reservas:paso_servicio"), {"servicio": self.servicio.pk})
        self.client.post(reverse("reservas:paso_fecha"), {"fecha": self.fecha.isoformat(), "hora": "10:00"})
        self.client.post(reverse("reservas:paso_confirmar"))
        self.assertTrue(Reserva.objects.filter(cliente=otro, hora_inicio=time(10)).exists())

    def test_anulacion_libera_hora(self):
        respuesta = self.client.get(reverse("reservas:anular", args=[self.reserva.numero]))
        self.assertContains(respuesta, "Anular la reserva")
        self.client.post(reverse("reservas:anular", args=[self.reserva.numero]))
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, Reserva.ANULADA)
        self.assertIn(time(10), horas_disponibles(self.fecha))

    def test_cliente_no_ve_reservas_de_otro(self):
        self.client.force_login(crear_cliente("cliente2").usuario)
        self.assertEqual(self.client.get(reverse("reservas:cambiar", args=[self.reserva.numero])).status_code, 404)
        self.assertEqual(self.client.post(reverse("reservas:anular", args=[self.reserva.numero])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("reservas:mis_reservas")), "Cambio de aceite")
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, Reserva.VIGENTE)

    def test_no_se_cambia_reserva_pasada(self):
        pasada = crear_reserva(self.cliente, self.servicio, timezone.localdate() - timedelta(days=3), time(10))
        respuesta = self.client.get(reverse("reservas:cambiar", args=[pasada.numero]), follow=True)
        self.assertContains(respuesta, "Solo se pueden cambiar reservas vigentes con fecha futura")
        self.client.post(reverse("reservas:anular", args=[pasada.numero]))
        pasada.refresh_from_db()
        self.assertEqual(pasada.estado, Reserva.VIGENTE)

    def test_empleado_anula_desde_la_agenda(self):
        self.client.force_login(crear_usuario("administrativo", "ADMINISTRATIVO"))
        self.client.post(reverse("agenda:anular", args=[self.reserva.numero]))
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, Reserva.ANULADA)
