"""HU16 · Generar orden de pedido · RF20, RF23 · RNF08 · CU10"""

from django.urls import reverse

from abastecimiento.models import OrdenPedido
from core.models import RegistroAuditoria

from .base import AbastecimientoTestCase


class GenerarOrdenTests(AbastecimientoTestCase):
    def post_orden(self, filas, extra=0):
        datos = {"proveedor": self.proveedor.pk, "observacion": ""} | self.formset(filas, extra=extra)
        return self.client.post(reverse("abastecimiento:orden_nueva"), datos)

    def test_ordenes_reciben_correlativo_ascendente(self):
        r1 = self.post_orden([(self.aceite, 10)])
        self.post_orden([(self.filtro, 5)])
        self.assertRedirects(r1, reverse("abastecimiento:orden", args=[1]))
        self.assertEqual(list(OrdenPedido.objects.order_by("numero").values_list("numero", flat=True)), [1, 2])
        orden = OrdenPedido.objects.get(numero=1)
        self.assertEqual((orden.creada_por, orden.proveedor), (self.empleado, self.proveedor))

    def test_empleado_no_habilitado_no_genera_orden(self):
        self.client.force_login(self.no_habilitado)
        self.assertEqual(self.client.get(reverse("abastecimiento:orden_nueva")).status_code, 403)
        self.assertEqual(self.post_orden([(self.aceite, 10)]).status_code, 403)
        self.assertFalse(OrdenPedido.objects.exists())

    def test_intento_no_habilitado_queda_en_log(self):
        self.client.force_login(self.no_habilitado)
        self.client.get(reverse("abastecimiento:orden_nueva"))
        registro = RegistroAuditoria.objects.get(operacion="ACCESO_DENEGADO")
        self.assertEqual(registro.usuario, self.no_habilitado)
        self.assertIn("RF23", registro.detalle["motivo"])

    def test_creacion_orden_queda_en_log(self):
        self.post_orden([(self.aceite, 10), (self.filtro, 5)])
        registro = RegistroAuditoria.objects.get(operacion="CREAR", entidad="OrdenPedido")
        self.assertEqual(registro.entidad_id, "1")
        self.assertEqual(len(registro.detalle["lineas"]), 2)

    def test_orden_sin_productos_es_rechazada(self):
        respuesta = self.post_orden([], extra=2)
        self.assertContains(respuesta, "La orden debe tener al menos un producto")
        self.assertFalse(OrdenPedido.objects.exists())

    def test_cantidad_cero_y_producto_repetido_son_rechazados(self):
        self.assertContains(self.post_orden([(self.aceite, 0)]), "La cantidad debe ser mayor que 0")
        self.assertContains(self.post_orden([(self.aceite, 1), (self.aceite, 2)]), "Producto repetido")
        self.assertFalse(OrdenPedido.objects.exists())
