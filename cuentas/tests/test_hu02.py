"""HU02 · Cuentas y perfiles · RF02, RF03 · RNF06, RNF07 · CU02"""

from django.test import TestCase
from django.urls import reverse

from core.menu import MENU, menu_para
from core.permisos import modulos_visibles
from core.models import RegistroAuditoria
from core.tests.fabricas import crear_empleado, crear_usuario
from cuentas.models import Usuario


class CuentasYPerfilesTests(TestCase):
    def setUp(self):
        self.admin = crear_usuario("admin", "ADMIN")
        crear_empleado(self.admin, solicita_productos=True, ejecuta_servicios=True)  # como en los datos demo
        self.mecanico = crear_usuario("mecanico", "MECANICO")

    def test_mecanico_no_entra_a_usuarios(self):
        self.client.force_login(self.mecanico)
        respuesta = self.client.get(reverse("cuentas:usuarios"))
        self.assertEqual(respuesta.status_code, 403)
        self.assertContains(respuesta, "Acceso denegado", status_code=403)

    def test_acceso_denegado_queda_en_log(self):
        self.client.force_login(self.mecanico)
        self.client.get(reverse("cuentas:usuarios"))
        registro = RegistroAuditoria.objects.get(operacion="ACCESO_DENEGADO")
        self.assertEqual(registro.usuario, self.mecanico)
        self.assertEqual(registro.entidad_id, "usuarios")
        self.assertEqual(registro.detalle["ruta"], reverse("cuentas:usuarios"))
        # El administrador ve el intento en /auditoria/.
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse("core:auditoria")), "Acceso denegado")

    def test_admin_entra_a_todos_los_modulos(self):
        """RNF07 · recorre todas las URLs del menú."""
        self.client.force_login(self.admin)
        for grupo in menu_para(modulos_visibles(self.admin)):
            for entrada in grupo["entradas"]:
                with self.subTest(url=entrada["url"]):
                    self.assertEqual(self.client.get(reverse(entrada["url"])).status_code, 200)
        # Ni siquiera los módulos que no están en su menú le dan "Acceso denegado".
        for _grupo, entradas in MENU:
            for _modulo, _etiqueta, nombre_url in entradas:
                with self.subTest(url=nombre_url):
                    self.assertNotEqual(self.client.get(reverse(nombre_url)).status_code, 403)
        self.assertFalse(RegistroAuditoria.objects.filter(operacion="ACCESO_DENEGADO").exists())

    def test_admin_crea_cuenta_con_perfil(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse("cuentas:nuevo_usuario"), {
            "username": "mecanico2", "first_name": "Mario", "last_name": "Pérez", "email": "m@x.cl",
            "perfil": "MECANICO", "password1": "Taller#2026x", "password2": "Taller#2026x",
        })
        self.assertRedirects(respuesta, reverse("cuentas:usuarios"))
        nuevo = Usuario.objects.get(username="mecanico2")
        self.assertEqual(nuevo.perfil, "MECANICO")
        self.assertTrue(nuevo.check_password("Taller#2026x"))
        # Con esa cuenta, no puede entrar al módulo de usuarios.
        self.client.force_login(nuevo)
        self.assertEqual(self.client.get(reverse("cuentas:usuarios")).status_code, 403)

    def test_no_se_crean_cuentas_cliente_desde_usuarios(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(reverse("cuentas:nuevo_usuario"), {
            "username": "x", "first_name": "X", "last_name": "Y", "email": "",
            "perfil": "CLIENTE", "password1": "Taller#2026x", "password2": "Taller#2026x",
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(Usuario.objects.filter(username="x").exists())

    def test_cuenta_desactivada_no_ingresa(self):
        crear_usuario("ana", "ADMINISTRATIVO", "ClaveSegura#2026")
        self.client.force_login(self.admin)
        cuenta = Usuario.objects.get(username="ana")
        self.client.post(reverse("cuentas:desactivar_usuario", args=[cuenta.pk]))
        cuenta.refresh_from_db()
        self.assertFalse(cuenta.is_active)
        self.client.logout()
        respuesta = self.client.post(reverse("cuentas:ingresar"), {"usuario": "ana", "contrasena": "ClaveSegura#2026"})
        self.assertContains(respuesta, "Usuario o contraseña incorrectos")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_admin_no_se_desactiva_a_si_mismo(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("cuentas:desactivar_usuario", args=[self.admin.pk]))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
