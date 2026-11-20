"""HU17 · Modificar o eliminar orden sin recepciones · RF21, RF22 · RNF08 · CU10"""

from decimal import Decimal

from django.urls import reverse

from abastecimiento import servicios as srv
from abastecimiento.models import OrdenPedido
from core.models import RegistroAuditoria

from .base import AbastecimientoTestCase


class ModificarEliminarOrdenTests(AbastecimientoTestCase):
    def setUp(self):
        super().setUp()
        self.orden = self.crear_orden()

    def recepcionar(self):
        l1, l2 = self.orden.lineas.order_by("id")
        srv.registrar_recepcion(self.orden, self.usuario, {l1.producto_id: Decimal("1")}, confirmar_diferencias=True)

    def datos_modificar(self, filas):
        return {"observacion": "corregida", "version_leida": self.orden.version} | self.formset(filas)

    def test_orden_con_recepcion_no_se_modifica(self):
        self.recepcionar()
        url = reverse("abastecimiento:orden_modificar", args=[self.orden.numero])
        respuesta = self.client.post(url, self.datos_modificar([(self.aceite, 99)]), follow=True)
        self.assertContains(respuesta, "No se puede modificar ni eliminar una orden con recepciones registradas")
        self.assertEqual(self.orden.lineas.get(producto=self.aceite).cantidad_solicitada, Decimal("10"))
        detalle = self.client.get(reverse("abastecimiento:orden", args=[self.orden.numero]))
        self.assertNotContains(detalle, url)  # el botón está oculto

    def test_orden_con_recepcion_no_se_elimina(self):
        self.recepcionar()
        respuesta = self.client.post(reverse("abastecimiento:orden_eliminar", args=[self.orden.numero]), follow=True)
        self.assertContains(respuesta, "No se puede modificar ni eliminar una orden con recepciones registradas")
        self.assertTrue(OrdenPedido.objects.filter(pk=self.orden.pk).exists())

    def test_numero_eliminado_no_se_reutiliza(self):
        ultima = self.crear_orden([(self.filtro, Decimal("1"))])  # N° 2, la última
        self.client.post(reverse("abastecimiento:orden_eliminar", args=[ultima.numero]))
        self.assertFalse(OrdenPedido.objects.filter(numero=ultima.numero).exists())
        nueva = self.crear_orden()
        self.assertEqual(nueva.numero, ultima.numero + 1)

    def test_modificacion_y_eliminacion_quedan_en_log(self):
        url = reverse("abastecimiento:orden_modificar", args=[self.orden.numero])
        self.client.post(url, self.datos_modificar([(self.aceite, 12)]))
        self.assertEqual(list(self.orden.lineas.values_list("cantidad_solicitada", flat=True)), [Decimal("12")])
        modificacion = RegistroAuditoria.objects.get(operacion="MODIFICAR", entidad="OrdenPedido")
        self.assertEqual(len(modificacion.detalle["anterior"]["lineas"]), 2)
        self.client.post(reverse("abastecimiento:orden_eliminar", args=[self.orden.numero]))
        eliminacion = RegistroAuditoria.objects.get(operacion="ELIMINAR", entidad="OrdenPedido")
        self.assertEqual(eliminacion.entidad_id, str(self.orden.numero))
        self.assertEqual(eliminacion.detalle["lineas"][0]["producto"], "ACE-10W40")

    def test_no_habilitado_no_corrige_ordenes(self):
        self.client.force_login(self.no_habilitado)
        self.assertEqual(self.client.post(reverse("abastecimiento:orden_eliminar", args=[self.orden.numero])).status_code, 403)
        self.assertTrue(OrdenPedido.objects.filter(pk=self.orden.pk).exists())
