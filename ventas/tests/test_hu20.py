"""HU20 · Modificar o anular boleta · RF27, RF28 · RNF08, RNF09 · CU12"""

from django.urls import NoReverseMatch, reverse

from core.models import RegistroAuditoria
from reservas.models import ServicioRealizado
from ventas import servicios as srv
from ventas.models import Boleta, EliminacionNoPermitida

from .base import VentasTestCase


class ModificarAnularBoletaTests(VentasTestCase):
    def setUp(self):
        super().setUp()
        self.boleta = srv.emitir_boleta(self.cliente, [self.r1, self.r2], self.usuario)
        self.lineas = list(self.boleta.lineas.all())

    def datos_modificar(self, **cambios):
        datos = {"observacion": "", "version_leida": self.boleta.version}
        datos.update({f"monto_{l.pk}": l.monto for l in self.lineas})
        datos.update(cambios)
        return datos

    def anular(self, motivo="Error en el servicio"):
        return self.client.post(reverse("ventas:boleta_anular", args=[self.boleta.numero]), {"motivo": motivo})

    def test_modificacion_guarda_valor_anterior_en_log(self):
        linea = self.lineas[0]
        self.client.post(reverse("ventas:boleta_modificar", args=[self.boleta.numero]),
                         self.datos_modificar(**{f"monto_{linea.pk}": 30000}))
        self.boleta.refresh_from_db()
        self.assertEqual(self.boleta.total, 50000)
        registro = RegistroAuditoria.objects.get(operacion="MODIFICAR", entidad="Boleta")
        self.assertEqual(registro.usuario, self.usuario)
        self.assertEqual(registro.detalle["cambios"]["línea 1 monto"]["anterior"], 35000)
        self.assertEqual(registro.detalle["cambios"]["línea 1 monto"]["nuevo"], 30000)
        self.assertEqual(registro.detalle["cambios"]["total"], {"anterior": 55000, "nuevo": 50000})
        ficha = self.client.get(reverse("ventas:boleta", args=[self.boleta.numero]))
        self.assertContains(ficha, "35000</s>")

    def test_edicion_concurrente_de_boleta_avisa_conflicto(self):
        url = reverse("ventas:boleta_modificar", args=[self.boleta.numero])
        datos = self.datos_modificar(observacion="primera")
        self.client.post(url, datos)
        respuesta = self.client.post(url, datos | {"observacion": "segunda"})
        self.assertContains(respuesta, "Otro usuario modificó este registro")

    def test_anulada_conserva_lineas_y_motivo(self):
        self.anular()
        self.boleta.refresh_from_db()
        self.assertEqual(self.boleta.estado, Boleta.ANULADA)
        self.assertEqual(self.boleta.motivo_anulacion, "Error en el servicio")
        self.assertEqual(self.boleta.anulada_por, self.usuario)
        self.assertEqual(self.boleta.total, 55000)
        self.assertEqual(self.boleta.lineas.count(), 2)
        ficha = self.client.get(reverse("ventas:boleta", args=[self.boleta.numero]))
        self.assertContains(ficha, "ANULADA")
        self.assertContains(ficha, "Error en el servicio")
        self.assertTrue(RegistroAuditoria.objects.filter(operacion="ANULAR", entidad_id=str(self.boleta.numero)).exists())

    def test_boleta_no_se_puede_eliminar(self):
        with self.assertRaises(EliminacionNoPermitida):
            self.boleta.delete()
        with self.assertRaises(EliminacionNoPermitida):
            Boleta.objects.all().delete()
        with self.assertRaises(NoReverseMatch):
            reverse("ventas:boleta_eliminar", args=[self.boleta.numero])
        self.assertEqual(self.client.post(f"/ventas/boletas/{self.boleta.numero}/eliminar/").status_code, 404)
        self.assertTrue(Boleta.objects.filter(pk=self.boleta.pk).exists())

    def test_anulacion_libera_servicios(self):
        self.anular()
        self.r1.refresh_from_db()
        self.assertEqual(self.r1.estado_documento, ServicioRealizado.PENDIENTE)
        nueva = srv.emitir_boleta(self.cliente, [self.r1], self.usuario)  # se pueden volver a boletear
        self.assertEqual(nueva.numero, 2)

    def test_anulacion_sin_motivo_es_rechazada(self):
        respuesta = self.anular("   ")
        self.assertContains(respuesta, "Indique el motivo de la anulación")
        self.boleta.refresh_from_db()
        self.assertEqual(self.boleta.estado, Boleta.EMITIDA)

    def test_boleta_anulada_no_se_modifica(self):
        self.anular()
        self.client.post(reverse("ventas:boleta_modificar", args=[self.boleta.numero]),
                         self.datos_modificar(observacion="cambio"))
        self.boleta.refresh_from_db()
        self.assertEqual(self.boleta.observacion, "")
        with self.assertRaises(srv.VentaNoPermitida):
            srv.modificar_boleta(self.boleta, self.usuario, "x", {})
