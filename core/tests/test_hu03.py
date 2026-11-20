"""HU03 · Ayuda en línea contextual · RF04"""

from django.test import TestCase
from django.urls import reverse

from core.models import SeccionAyuda
from core.tests.fabricas import crear_cliente, crear_usuario


class AyudaTests(TestCase):
    def setUp(self):
        for modulo, titulo in [("clientes", "Fichas de clientes"), ("reserva_web", "Reservar hora"), ("ventas", "Boletas y facturas")]:
            SeccionAyuda.objects.create(modulo=modulo, titulo=titulo, contenido=f"Pasos de {titulo}.")

    def test_ayuda_muestra_seccion_del_modulo_actual(self):
        self.client.force_login(crear_usuario("administrativo", "ADMINISTRATIVO"))
        for url, titulo in [(reverse("clientes:lista"), "Fichas de clientes"), (reverse("ventas:boletas"), "Boletas y facturas")]:
            with self.subTest(url=url):
                respuesta = self.client.get(url)
                self.assertContains(respuesta, 'aria-controls="panel-ayuda"')
                self.assertContains(respuesta, f"Ayuda: {titulo}")
                self.assertContains(respuesta, f"Pasos de {titulo}.")
        self.client.force_login(crear_cliente("cliente1").usuario)
        self.assertContains(self.client.get(reverse("reservas:paso_servicio")), "Ayuda: Reservar hora")

    def test_modulo_sin_seccion_muestra_manual_general(self):
        self.client.force_login(crear_usuario("admin", "ADMIN"))
        respuesta = self.client.get(reverse("catalogo:productos"))  # catálogo no tiene sección en este test
        self.assertContains(respuesta, "no tiene una sección propia en el manual")
        self.assertContains(respuesta, reverse("core:ayuda"))

    def test_manual_completo_es_publico(self):
        respuesta = self.client.get(reverse("core:ayuda"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Boletas y facturas")
