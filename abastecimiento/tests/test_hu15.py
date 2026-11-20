"""HU15 · Proveedores · RF19 · CU09"""

from django.urls import reverse

from abastecimiento.forms import OrdenForm
from abastecimiento.models import Proveedor
from core.tests.fabricas import crear_proveedor
from core.validadores import rut_con_dv

from .base import AbastecimientoTestCase


class ProveedoresTests(AbastecimientoTestCase):
    def datos(self, **cambios):
        return {"rut": rut_con_dv(76111222), "razon_social": "Frenos Chile SpA", "nombre_contacto": "Marco",
                "telefono": "", "email": "", "rubro": "Frenos", "activo": "on"} | cambios

    def test_proveedor_activo_aparece_en_orden(self):
        respuesta = self.client.post(reverse("abastecimiento:proveedor_nuevo"), self.datos())
        nuevo = Proveedor.objects.get(razon_social="Frenos Chile SpA")
        self.assertRedirects(respuesta, reverse("abastecimiento:proveedor", args=[nuevo.pk]))
        self.assertIn(nuevo, OrdenForm().fields["proveedor"].queryset)

    def test_proveedor_inactivo_no_aparece(self):
        inactivo = crear_proveedor("Viejo proveedor", activo=False)
        self.assertNotIn(inactivo, OrdenForm().fields["proveedor"].queryset)

    def test_rut_proveedor_duplicado_es_rechazado(self):
        respuesta = self.client.post(reverse("abastecimiento:proveedor_nuevo"), self.datos(rut=self.proveedor.rut))
        self.assertContains(respuesta, "Ya existe un proveedor con ese RUT")
        self.assertEqual(Proveedor.objects.count(), 1)

    def test_buscador_por_rubro(self):
        crear_proveedor("Baterías Maipú", rubro="Baterías y eléctrico")
        respuesta = self.client.get(reverse("abastecimiento:proveedores"), {"q": "eléctrico"})
        self.assertContains(respuesta, "Baterías Maipú")
        self.assertNotContains(respuesta, "Lubricantes del Sur")
