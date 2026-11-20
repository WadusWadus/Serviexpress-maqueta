"""HU08 · Reservar hora por Internet · RF10, RF11 · RNF18, RNF19 · CU04"""

from datetime import time, timedelta

from django.test import TestCase
from django.urls import reverse

from core.tests.fabricas import (crear_cliente, crear_reserva, crear_servicio, crear_usuario, proximo_dia_habil)
from reservas.models import DiaFestivo, Reserva
from reservas.servicios import fechas_ofrecidas, horas_disponibles


class ReservaWebTests(TestCase):
    def setUp(self):
        self.cliente = crear_cliente("cliente1")
        self.servicio = crear_servicio("Cambio de aceite", 35000)
        self.client.force_login(self.cliente.usuario)
        self.fecha = proximo_dia_habil()

    def reservar_hasta_confirmar(self, fecha=None, hora="10:00"):
        fecha = fecha or self.fecha
        self.client.post(reverse("reservas:paso_servicio"), {"servicio": self.servicio.pk})
        return self.client.post(reverse("reservas:paso_fecha"), {"fecha": fecha.isoformat(), "hora": hora})

    def test_flujo_reserva_completo_en_tres_pasos(self):
        """RNF18 · servicio → fecha y hora → confirmar: 3 pantallas."""
        pantallas = set()
        r1 = self.client.get(reverse("reservas:paso_servicio"))
        pantallas.add(r1.request["PATH_INFO"])
        r2 = self.client.post(reverse("reservas:paso_servicio"), {"servicio": self.servicio.pk}, follow=True)
        pantallas.add(r2.request["PATH_INFO"])
        r3 = self.client.post(reverse("reservas:paso_fecha"), {"fecha": self.fecha.isoformat(), "hora": "10:00"}, follow=True)
        pantallas.add(r3.request["PATH_INFO"])
        self.assertContains(r3, "Confirme su reserva")
        final = self.client.post(reverse("reservas:paso_confirmar"), follow=True)
        reserva = Reserva.objects.get()
        self.assertContains(final, f"Reserva N° {reserva.numero} registrada")
        self.assertEqual(final.request["PATH_INFO"], reverse("reservas:mis_reservas"))
        self.assertEqual(len(pantallas), 3)
        self.assertEqual((reserva.cliente, reserva.fecha, reserva.hora_inicio, reserva.canal),
                         (self.cliente, self.fecha, time(10), Reserva.WEB))

    def test_pantallas_de_reserva_son_responsivas(self):
        """RNF19 · viewport móvil y sin anchos fijos (se revisa a mano a 360 px)."""
        respuesta = self.client.get(reverse("reservas:paso_servicio"))
        self.assertContains(respuesta, 'name="viewport" content="width=device-width, initial-scale=1"')

    def test_festivo_no_aparece_disponible(self):
        DiaFestivo.objects.create(fecha=self.fecha, descripcion="Festivo de prueba")
        self.assertEqual(horas_disponibles(self.fecha), [])
        self.assertNotIn(self.fecha, fechas_ofrecidas())
        self.client.post(reverse("reservas:paso_servicio"), {"servicio": self.servicio.pk})
        respuesta = self.client.get(reverse("reservas:paso_fecha"))
        self.assertNotContains(respuesta, f"?fecha={self.fecha.isoformat()}")

    def test_reserva_en_festivo_forzada_es_rechazada(self):
        """Cierra el criterio pendiente de HU09: aunque se fuerce la fecha, el servidor la rechaza."""
        DiaFestivo.objects.create(fecha=self.fecha, descripcion="Festivo de prueba")
        respuesta = self.reservar_hasta_confirmar()
        self.assertContains(respuesta, "Fecha no disponible: día festivo")
        respuesta = self.client.get(reverse("reservas:paso_fecha"), {"fecha": self.fecha.isoformat()})
        self.assertContains(respuesta, "Fecha no disponible: día festivo")
        self.assertFalse(Reserva.objects.exists())

    def test_hora_ocupada_no_se_ofrece(self):
        otro = crear_cliente("cliente2")
        crear_reserva(otro, self.servicio, self.fecha, time(10))
        self.assertNotIn(time(10), horas_disponibles(self.fecha))
        self.assertIn(time(11), horas_disponibles(self.fecha))
        respuesta = self.reservar_hasta_confirmar(hora="10:00")
        self.assertContains(respuesta, "Hora no disponible")

    def test_hora_tomada_al_confirmar_vuelve_a_elegir(self):
        self.reservar_hasta_confirmar(hora="10:00")
        crear_reserva(crear_cliente("cliente2"), self.servicio, self.fecha, time(10))  # otra persona se adelanta
        respuesta = self.client.post(reverse("reservas:paso_confirmar"))
        self.assertRedirects(respuesta, f"{reverse('reservas:paso_fecha')}?fecha={self.fecha.isoformat()}",
                             fetch_redirect_response=False)
        siguiente = self.client.get(respuesta.url)
        self.assertContains(siguiente, "La hora elegida acaba de ser reservada por otra persona. Elija otra.")
        self.assertEqual(Reserva.objects.filter(cliente=self.cliente).count(), 0)

    def test_servicio_desactivado_no_se_puede_reservar(self):
        self.servicio.activo = False
        self.servicio.save()
        respuesta = self.client.get(reverse("reservas:paso_servicio"))
        self.assertNotContains(respuesta, "Cambio de aceite")
        self.client.post(reverse("reservas:paso_servicio"), {"servicio": self.servicio.pk})
        self.assertNotIn("servicio_id", self.client.session.get("reserva_en_curso", {}))

    def test_fecha_pasada_o_fuera_de_plazo_es_rechazada(self):
        for fecha in [self.fecha - timedelta(days=40), self.fecha + timedelta(days=60)]:
            respuesta = self.reservar_hasta_confirmar(fecha=fecha)
            self.assertContains(respuesta, "Fecha no disponible")
        self.assertFalse(Reserva.objects.exists())

    def test_empleado_reserva_en_local_para_un_cliente(self):
        self.client.force_login(crear_usuario("administrativo", "ADMINISTRATIVO"))
        busqueda = self.client.get(reverse("agenda:nueva"), {"q": self.cliente.rut})
        self.assertContains(busqueda, self.cliente.nombre_completo)
        self.client.post(reverse("agenda:nueva"), {"cliente": self.cliente.pk})
        self.client.post(reverse("agenda:paso_servicio"), {"servicio": self.servicio.pk})
        self.client.post(reverse("agenda:paso_fecha"), {"fecha": self.fecha.isoformat(), "hora": "11:00"})
        respuesta = self.client.post(reverse("agenda:paso_confirmar"), follow=True)
        reserva = Reserva.objects.get()
        self.assertEqual((reserva.cliente, reserva.canal), (self.cliente, Reserva.LOCAL))
        self.assertContains(respuesta, f"Reserva N° {reserva.numero} registrada")
        self.assertContains(self.client.get(reverse("agenda:lista")), self.cliente.nombre_completo)

    def test_cliente_no_entra_a_la_agenda(self):
        self.assertEqual(self.client.get(reverse("agenda:lista")).status_code, 403)
