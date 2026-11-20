"""HU04 · Registrar ficha de cliente · RF05 · CU03"""

from django.test import TestCase
from django.urls import reverse

from clientes.models import Cliente
from core.tests.fabricas import crear_cliente, crear_usuario
from core.validadores import rut_con_dv
from cuentas.models import Usuario

CLAVE = "Cliente#2026x"


class FichaClienteTests(TestCase):
    def setUp(self):
        self.client.force_login(crear_usuario("administrativo", "ADMINISTRATIVO"))

    def datos(self, **cambios):
        return {"rut": "12.345.678-5", "nombres": "María", "apellidos": "González", "telefono": "+56911112222",
                "email": "maria@correo.cl", "direccion": "Maipú", "usuario": "mgonzalez",
                "password1": CLAVE, "password2": CLAVE} | cambios

    def test_ficha_cliente_se_guarda(self):
        respuesta = self.client.post(reverse("clientes:nuevo"), self.datos())
        cliente = Cliente.objects.get()
        self.assertRedirects(respuesta, reverse("clientes:ficha", args=[cliente.pk]))
        self.assertEqual(cliente.rut, "12345678-5")
        self.assertEqual(cliente.usuario.perfil, Usuario.CLIENTE)

    def test_cliente_nuevo_puede_ingresar(self):
        self.client.post(reverse("clientes:nuevo"), self.datos())
        self.client.logout()
        respuesta = self.client.post(reverse("cuentas:ingresar"), {"usuario": "mgonzalez", "contrasena": CLAVE})
        self.assertRedirects(respuesta, reverse("core:panel"))

    def test_rut_duplicado_es_rechazado(self):
        crear_cliente(rut=rut_con_dv(12345678))
        respuesta = self.client.post(reverse("clientes:nuevo"), self.datos())
        self.assertContains(respuesta, "RUT")
        self.assertEqual(Cliente.objects.count(), 1)
        self.assertFalse(Usuario.objects.filter(username="mgonzalez").exists())  # tampoco la cuenta

    def test_rut_invalido_es_rechazado(self):
        respuesta = self.client.post(reverse("clientes:nuevo"), self.datos(rut="12345678-0"))
        self.assertContains(respuesta, "dígito verificador")
        self.assertFalse(Cliente.objects.exists())

    def test_mecanico_no_registra_clientes(self):
        self.client.force_login(crear_usuario("mecanico", "MECANICO"))
        self.assertEqual(self.client.get(reverse("clientes:nuevo")).status_code, 403)
