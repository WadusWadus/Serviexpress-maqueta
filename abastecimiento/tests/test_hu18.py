"""HU18 · Recepcionar productos contra la orden · RF24, RF25 · CU11"""

from decimal import Decimal

from django.urls import reverse

from abastecimiento.models import Recepcion

from .base import AbastecimientoTestCase


class RecepcionTests(AbastecimientoTestCase):
    def setUp(self):
        super().setUp()
        self.orden = self.crear_orden()  # aceite 10, filtro 5
        self.l_aceite, self.l_filtro = self.orden.lineas.order_by("id")
        self.url = reverse("abastecimiento:recepcionar", args=[self.orden.numero])

    def datos(self, aceite="10", filtro="5", **extra):
        return {f"cantidad_{self.l_aceite.pk}": aceite, f"cantidad_{self.l_filtro.pk}": filtro, "observacion": ""} | extra

    def test_producto_no_solicitado_es_rechazado(self):
        respuesta = self.client.post(self.url, self.datos(codigo_extra_1="BATERIA", cantidad_extra_1="1"))
        self.assertContains(respuesta, f"Producto no solicitado en la orden N° {self.orden.numero}")

    def test_rechazo_no_guarda_la_recepcion(self):
        self.client.post(self.url, self.datos(codigo_extra_1="bateria", cantidad_extra_1="1", confirmar="1"))
        self.assertFalse(Recepcion.objects.exists())
        self.assertFalse(self.orden.tiene_recepciones)

    def test_diferencia_de_cantidad_pide_confirmacion(self):
        respuesta = self.client.post(self.url, self.datos(aceite="8"))
        self.assertContains(respuesta, "La cantidad recibida de Aceite 10W-40 (8) difiere de la pendiente (10). ¿Confirma la recepción?")
        self.assertContains(respuesta, "Confirmar con diferencias")
        self.assertFalse(Recepcion.objects.exists())

    def test_confirmar_con_diferencias_guarda(self):
        respuesta = self.client.post(self.url, self.datos(aceite="8", confirmar="1"))
        self.assertRedirects(respuesta, reverse("abastecimiento:orden", args=[self.orden.numero]))
        self.assertEqual(Recepcion.objects.count(), 1)
        self.assertEqual(self.l_aceite.cantidad_pendiente, Decimal("2"))

    def test_orden_inexistente_avisa(self):
        respuesta = self.client.get(reverse("abastecimiento:recepcion_nueva"), {"numero": 999})
        self.assertContains(respuesta, "La orden N° 999 no existe")
        existente = self.client.get(reverse("abastecimiento:recepcion_nueva"), {"numero": self.orden.numero})
        self.assertRedirects(existente, self.url)

    def test_recepcion_actualiza_pendientes(self):
        self.client.post(self.url, self.datos())  # todo igual a lo pendiente: se guarda sin advertencia
        self.assertEqual(self.l_aceite.cantidad_pendiente, 0)
        self.assertEqual(self.l_filtro.cantidad_pendiente, 0)
        self.orden.refresh_from_db()
        self.assertTrue(self.orden.tiene_recepciones)
        self.assertEqual(self.orden.estado, self.orden.COMPLETA)

    def test_producto_de_la_orden_agregado_por_codigo_se_suma(self):
        self.client.post(self.url, self.datos(aceite="6", codigo_extra_1="ace-10w40", cantidad_extra_1="4"))
        self.assertEqual(self.l_aceite.cantidad_recibida, Decimal("10"))
