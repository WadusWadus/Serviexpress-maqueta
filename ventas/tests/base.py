from django.test import TestCase

from core.tests.fabricas import crear_cliente, crear_realizado, crear_servicio, crear_usuario


class VentasTestCase(TestCase):
    def setUp(self):
        self.usuario = crear_usuario("administrativo", "ADMINISTRATIVO")
        self.client.force_login(self.usuario)
        self.cliente = crear_cliente("cliente1", nombres="María", apellidos="González")
        self.aceite = crear_servicio("Cambio de aceite", 35000)
        self.frenos = crear_servicio("Revisión de frenos", 20000)
        self.r1 = crear_realizado(self.cliente, self.aceite)
        self.r2 = crear_realizado(self.cliente, self.frenos, empleado=self.r1.empleado)
