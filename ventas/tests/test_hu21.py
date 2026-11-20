"""HU21 · Registrar factura · RF29 · RNF08 · CU13"""

from django.urls import reverse

from core.models import RegistroAuditoria
from reservas.models import ServicioRealizado
from ventas.models import Factura

from .base import VentasTestCase


class RegistrarFacturaTests(VentasTestCase):
    def facturar(self, *realizados):
        url = f"{reverse('ventas:factura_nueva')}?cliente={self.cliente.pk}"
        return self.client.post(url, {
            "servicios": [r.pk for r in realizados], "rut_facturacion": "76.123.456-0",
            "razon_social": "Transportes González SpA", "giro": "Transporte", "direccion_facturacion": "Maipú",
        })

    def test_factura_asociada_a_servicio_y_cliente(self):
        respuesta = self.facturar(self.r1)
        factura = Factura.objects.get()
        self.assertRedirects(respuesta, reverse("ventas:factura", args=[factura.numero]))
        self.assertEqual(factura.cliente, self.cliente)
        self.assertEqual(factura.lineas.get().servicio_realizado, self.r1)
        self.assertEqual((factura.neto + factura.iva, factura.total), (35000, 35000))
        self.assertEqual(factura.rut_facturacion, "76123456-0")
        self.r1.refresh_from_db()
        self.assertEqual(self.r1.estado_documento, ServicioRealizado.DOCUMENTADO)

    def test_servicio_facturado_no_aparece_para_boleta(self):
        self.facturar(self.r1)
        respuesta = self.client.get(reverse("ventas:boleta_nueva"), {"cliente": self.cliente.pk})
        self.assertNotIn(self.r1, respuesta.context["pendientes"])

    def test_registro_factura_queda_en_log(self):
        self.facturar(self.r1)
        self.assertTrue(RegistroAuditoria.objects.filter(operacion="CREAR", entidad="Factura", entidad_id="1").exists())

    def test_rut_de_facturacion_invalido_es_rechazado(self):
        url = f"{reverse('ventas:factura_nueva')}?cliente={self.cliente.pk}"
        respuesta = self.client.post(url, {"servicios": [self.r1.pk], "rut_facturacion": "76123456-1",
                                           "razon_social": "X", "giro": "Y", "direccion_facturacion": "Z"})
        self.assertContains(respuesta, "dígito verificador")
        self.assertFalse(Factura.objects.exists())
