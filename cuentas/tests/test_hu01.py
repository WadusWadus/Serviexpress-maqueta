"""HU01 · Iniciar sesión · RF01 · RNF05, RNF10, RNF11 · CU01"""

from datetime import timedelta

from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import RegistroAuditoria
from core.tests.fabricas import crear_usuario

CLAVE = "ClaveSegura#2026"


class IngresoTests(TestCase):
    url = reverse("cuentas:ingresar")

    def ingresar(self, usuario, clave=CLAVE, **extra):
        return self.client.post(self.url, {"usuario": usuario, "contrasena": clave, **extra})

    def test_ingreso_correcto_redirige_al_panel(self):
        for perfil in ["ADMIN", "ADMINISTRATIVO", "MECANICO", "CLIENTE"]:
            with self.subTest(perfil=perfil):
                usuario = crear_usuario(f"u_{perfil.lower()}", perfil, CLAVE, intentos_fallidos=2)
                respuesta = self.ingresar(usuario.username)
                self.assertRedirects(respuesta, reverse("core:panel"))
                usuario.refresh_from_db()
                self.assertEqual(usuario.intentos_fallidos, 0)
                self.client.post(reverse("cuentas:salir"))

    def test_ingreso_incorrecto_muestra_error(self):
        crear_usuario("ana", "ADMINISTRATIVO", CLAVE)
        respuesta = self.ingresar("ana", "otra-clave")
        self.assertContains(respuesta, "Usuario o contraseña incorrectos")
        respuesta = self.ingresar("no-existe", CLAVE)  # no se dice cuál de los dos falló
        self.assertContains(respuesta, "Usuario o contraseña incorrectos")
        self.assertEqual(RegistroAuditoria.objects.filter(operacion="LOGIN_FALLIDO").count(), 2)

    def test_bloqueo_tras_cinco_intentos(self):
        usuario = crear_usuario("cliente2", "CLIENTE", CLAVE)
        for _ in range(4):
            self.assertContains(self.ingresar("cliente2", "mala"), "Usuario o contraseña incorrectos")
        respuesta = self.ingresar("cliente2", "mala")
        self.assertContains(respuesta, "Cuenta bloqueada por 15 minutos por intentos fallidos")
        usuario.refresh_from_db()
        self.assertTrue(usuario.esta_bloqueado())
        self.assertAlmostEqual(usuario.bloqueado_hasta, timezone.now() + timedelta(minutes=15),
                               delta=timedelta(seconds=30))
        self.assertTrue(RegistroAuditoria.objects.filter(operacion="BLOQUEO", entidad_id="cliente2").exists())
        # Bloqueada, ni siquiera la contraseña correcta permite entrar.
        self.assertContains(self.ingresar("cliente2"), "Cuenta bloqueada")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_bloqueo_expira_a_los_15_minutos(self):
        usuario = crear_usuario("cliente2", "CLIENTE", CLAVE)
        usuario.bloqueado_hasta = timezone.now() + timedelta(minutes=1)
        usuario.save()
        self.assertContains(self.ingresar("cliente2"), "Cuenta bloqueada")
        usuario.bloqueado_hasta = timezone.now() - timedelta(seconds=1)  # pasaron los 15 minutos
        usuario.save()
        self.assertRedirects(self.ingresar("cliente2"), reverse("core:panel"))

    def test_contrasena_guardada_con_hash(self):
        usuario = crear_usuario("ana", "ADMINISTRATIVO", CLAVE)
        self.assertNotEqual(usuario.password, CLAVE)
        self.assertTrue(usuario.password.startswith("pbkdf2_sha256$"))
        self.assertTrue(usuario.check_password(CLAVE))

    def test_sesion_expira_por_inactividad(self):
        """RNF11 · 15 minutos sin actividad cierran la sesión y se avisa al volver."""
        self.assertEqual(settings.SESSION_COOKIE_AGE, 15 * 60)
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)
        crear_usuario("ana", "ADMINISTRATIVO", CLAVE)
        self.ingresar("ana")
        Session.objects.all().delete()  # equivale a que la sesión expiró
        respuesta = self.client.get(reverse("core:panel"), follow=True)
        self.assertContains(respuesta, "Su sesión se cerró por inactividad")
        self.assertEqual(respuesta.redirect_chain[-1][0].split("?")[0], self.url)

    def test_vistas_internas_exigen_sesion(self):
        self.assertEqual(self.client.get(reverse("core:inicio")).status_code, 200)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        respuesta = self.client.get(reverse("core:panel"))
        self.assertRedirects(respuesta, f"{self.url}?next={reverse('core:panel')}")

    def test_mecanico_ve_solo_su_menu(self):
        crear_usuario("mecanico", "MECANICO", CLAVE)
        self.ingresar("mecanico")
        respuesta = self.client.get(reverse("core:panel"))
        self.assertNotContains(respuesta, reverse("cuentas:usuarios"))
        self.assertNotContains(respuesta, reverse("clientes:lista"))
