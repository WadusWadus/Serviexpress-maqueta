"""HU19 · Generar boleta · RF26 · RNF08 · CU12"""

from django.urls import reverse

from core.models import RegistroAuditoria
from reservas.models import ServicioRealizado
from ventas.models import Boleta

from .base import VentasTestCase


class GenerarBoletaTests(VentasTestCase):
    def emitir(self, *realizados, **extra):
        url = f"{reverse('ventas:boleta_nueva')}?cliente={self.cliente.pk}"
        return self.client.post(url, {"servicios": [r.pk for r in realizados], "observacion": "", **extra})

    def test_boleta_toma_datos_de_servicio_y_cliente(self):
        respuesta = self.emitir(self.r1, self.r2)
        boleta = Boleta.objects.get()
        self.assertRedirects(respuesta, reverse("ventas:boleta", args=[boleta.numero]))
        self.assertEqual(boleta.cliente, self.cliente)
        self.assertEqual(boleta.total, 55000)
        self.assertEqual([(l.servicio_realizado, l.monto) for l in boleta.lineas.all()], [(self.r1, 35000), (self.r2, 20000)])
        impresa = self.client.get(reverse("ventas:boleta", args=[boleta.numero]))
        self.assertContains(impresa, "María González")
        self.assertContains(impresa, "$55.000")
        self.assertContains(impresa, "window.print()")

    def test_servicio_queda_documentado(self):
        self.emitir(self.r1)
        self.r1.refresh_from_db()
        self.r2.refresh_from_db()
        self.assertEqual(self.r1.estado_documento, ServicioRealizado.DOCUMENTADO)
        self.assertEqual(self.r2.estado_documento, ServicioRealizado.PENDIENTE)

    def test_numero_boleta_correlativo(self):
        self.emitir(self.r1)
        self.emitir(self.r2)
        self.assertEqual(list(Boleta.objects.order_by("numero").values_list("numero", flat=True)), [1, 2])

    def test_emision_queda_en_log(self):
        self.emitir(self.r1)
        registro = RegistroAuditoria.objects.get(operacion="CREAR", entidad="Boleta")
        self.assertEqual((registro.entidad_id, registro.usuario), ("1", self.usuario))

    def test_servicio_documentado_no_aparece_pendiente(self):
        self.emitir(self.r1)
        respuesta = self.client.get(reverse("ventas:boleta_nueva"), {"cliente": self.cliente.pk})
        self.assertNotIn(self.r1, respuesta.context["pendientes"])
        self.assertIn(self.r2, respuesta.context["pendientes"])
        self.emitir(self.r1)  # forzarlo no sirve
        self.assertEqual(Boleta.objects.count(), 1)

    def test_boleta_sin_servicios_es_rechazada(self):
        respuesta = self.emitir()
        self.assertContains(respuesta, "Marque al menos un servicio")
        self.assertFalse(Boleta.objects.exists())
