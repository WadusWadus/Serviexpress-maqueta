"""HU06 · Habilitar clientes para fiado · RF07 · CU14"""

from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from core.tests.fabricas import crear_cliente, crear_usuario


class HabilitarFiadoTests(TestCase):
    def setUp(self):
        self.admin = crear_usuario("admin", "ADMIN")
        self.cliente1 = crear_cliente("cliente1")
        self.cliente2 = crear_cliente("cliente2")
        self.client.force_login(self.admin)

    def test_solo_habilitados_tienen_opcion_fiado(self):
        self.client.post(reverse("clientes:fiado_cambiar", args=[self.cliente1.pk]))
        self.assertEqual(list(Cliente.objects.habilitados_fiado()), [self.cliente1])
        ficha1 = self.client.get(reverse("clientes:ficha", args=[self.cliente1.pk]))
        ficha2 = self.client.get(reverse("clientes:ficha", args=[self.cliente2.pk]))
        self.assertContains(ficha1, "Habilitado para fiado")
        self.assertNotContains(ficha2, "Habilitado para fiado")
        # Volver a pulsar el interruptor lo deshabilita.
        self.client.post(reverse("clientes:fiado_cambiar", args=[self.cliente1.pk]))
        self.assertFalse(Cliente.objects.habilitados_fiado().exists())

    def test_administrativo_no_puede_habilitar_fiado(self):
        self.client.force_login(crear_usuario("administrativo", "ADMINISTRATIVO"))
        self.assertEqual(self.client.get(reverse("clientes:fiado")).status_code, 403)
        self.assertEqual(self.client.post(reverse("clientes:fiado_cambiar", args=[self.cliente1.pk])).status_code, 403)
        self.cliente1.refresh_from_db()
        self.assertFalse(self.cliente1.fiado_habilitado)
