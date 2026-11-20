"""HU14 · Empleados y su función · RF18 · CU17"""

from django.test import TestCase
from django.urls import reverse

from core.tests.fabricas import crear_usuario
from core.validadores import rut_con_dv
from personal.models import Empleado


class EmpleadosTests(TestCase):
    def setUp(self):
        self.client.force_login(crear_usuario("admin", "ADMIN"))

    def datos(self, **cambios):
        return {"rut": rut_con_dv(17000111), "nombres": "Diego", "apellidos": "Paredes", "telefono": "",
                "usuario": "", "activo": "on"} | cambios

    def test_empleado_sin_funcion_es_rechazado(self):
        respuesta = self.client.post(reverse("personal:nuevo"), self.datos())
        self.assertContains(respuesta, "Marque al menos una función: solicitar productos o ejecutar servicios")
        self.assertFalse(Empleado.objects.exists())

    def test_empleado_con_una_funcion_se_guarda(self):
        respuesta = self.client.post(reverse("personal:nuevo"), self.datos(ejecuta_servicios="on"))
        self.assertRedirects(respuesta, reverse("personal:lista"))
        empleado = Empleado.objects.get()
        self.assertTrue(empleado.ejecuta_servicios)
        self.assertFalse(empleado.solicita_productos)
        self.assertContains(self.client.get(reverse("personal:lista")), "Ejecuta servicios")

    def test_rut_invalido_es_rechazado(self):
        respuesta = self.client.post(reverse("personal:nuevo"), self.datos(rut="17000111-0", ejecuta_servicios="on"))
        self.assertContains(respuesta, "dígito verificador")

    def test_administrativo_no_entra_a_personal(self):
        self.client.force_login(crear_usuario("ana", "ADMINISTRATIVO"))
        self.assertEqual(self.client.get(reverse("personal:lista")).status_code, 403)
