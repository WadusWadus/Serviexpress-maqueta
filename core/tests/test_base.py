"""S0 · Base común: correlativos (5.5) y auditoría (5.3)."""

from django.core.management import call_command
from django.test import TestCase

from core.auditoria import registrar
from core.correlativos import siguiente
from core.models import Correlativo, RegistroAuditoria
from core.validadores import normalizar_rut, rut_con_dv, validar_rut
from django.core.exceptions import ValidationError


class BaseComunTests(TestCase):
    def test_correlativo_no_reutiliza(self):
        """RF22 · Los números siguen subiendo aunque se borre el último documento."""
        self.assertEqual(siguiente("orden_pedido"), 1)
        self.assertEqual(siguiente("orden_pedido"), 2)
        self.assertEqual(siguiente("boleta"), 1)  # cada correlativo es independiente
        self.assertEqual(siguiente("orden_pedido"), 3)
        self.assertEqual(Correlativo.objects.get(nombre="orden_pedido").ultimo, 3)

    def test_registrar_auditoria(self):
        registro = registrar(None, RegistroAuditoria.CREAR, "Boleta", 7, {"total": 1000})
        self.assertEqual(RegistroAuditoria.objects.count(), 1)
        self.assertIsNone(registro.usuario)
        self.assertEqual(registro.entidad_id, "7")
        self.assertEqual(registro.detalle, {"total": 1000})

    def test_validacion_rut(self):
        self.assertEqual(normalizar_rut("12.345.678-5"), "12345678-5")
        validar_rut(rut_con_dv(12345678))
        validar_rut("11.111.111-1")
        with self.assertRaises(ValidationError):
            validar_rut("12345678-0")

    def test_cargar_demo_corre_dos_veces(self):
        call_command("cargar_demo", verbosity=0, stdout=open("/dev/null", "w"))
        call_command("cargar_demo", verbosity=0, stdout=open("/dev/null", "w"))



class IngresoSinCredencialesTests(TestCase):
    """La pantalla de ingreso no muestra usuarios ni contraseñas (el sitio está publicado)."""

    def test_ingreso_no_muestra_credenciales(self):
        from django.test import override_settings
        from django.urls import reverse
        with override_settings(DEMO=True):
            respuesta = self.client.get(reverse("cuentas:ingresar"))
        self.assertNotContains(respuesta, "Demo2026!")
        self.assertNotContains(respuesta, "credenciales-demo")
