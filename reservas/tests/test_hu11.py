"""HU11 · Registrar servicio realizado · RF14 · CU06"""

from datetime import time

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import RegistroAuditoria
from core.tests.fabricas import crear_cliente, crear_empleado, crear_reserva, crear_servicio, crear_usuario
from reservas.models import Reserva, ServicioRealizado


class RegistrarServicioTests(TestCase):
    def setUp(self):
        self.usuario = crear_usuario("mecanico", "MECANICO")
        self.mecanico = crear_empleado(self.usuario, ejecuta_servicios=True)
        self.cliente = crear_cliente("cliente1")
        self.servicio = crear_servicio("Cambio de aceite")
        self.client.force_login(self.usuario)

    def test_servicio_realizado_guarda_cliente_fecha_y_mecanico(self):
        self.client.post(reverse("atencion:registrar"), {"rut": self.cliente.rut, "servicio": self.servicio.pk,
                                                        "observacion": "Sin novedad"})
        realizado = ServicioRealizado.objects.get()
        self.assertEqual(realizado.cliente, self.cliente)
        self.assertEqual(realizado.fecha, timezone.localdate())
        self.assertEqual(realizado.empleado, self.mecanico)
        self.assertEqual(realizado.estado_documento, ServicioRealizado.PENDIENTE)

    def test_registro_desde_reserva_la_marca_atendida(self):
        reserva = crear_reserva(self.cliente, self.servicio, timezone.localdate(), time(17))
        inicio = self.client.get(reverse("atencion:inicio"))
        self.assertContains(inicio, f"?reserva={reserva.numero}")
        respuesta = self.client.get(reverse("atencion:registrar"), {"reserva": reserva.numero})
        self.assertContains(respuesta, self.cliente.nombre_completo)
        self.client.post(f"{reverse('atencion:registrar')}?reserva={reserva.numero}", {"observacion": ""})
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, Reserva.ATENDIDA)
        realizado = ServicioRealizado.objects.get()
        self.assertEqual((realizado.reserva, realizado.servicio), (reserva, self.servicio))

    def test_registro_sin_reserva(self):
        respuesta = self.client.post(reverse("atencion:registrar"), {"rut": self.cliente.rut, "servicio": self.servicio.pk})
        self.assertRedirects(respuesta, reverse("atencion:realizados"))
        self.assertIsNone(ServicioRealizado.objects.get().reserva)

    def test_cliente_no_registrado_muestra_derivacion(self):
        respuesta = self.client.post(reverse("atencion:registrar"), {"rut": "11.111.111-1", "servicio": self.servicio.pk})
        self.assertContains(respuesta, "Cliente no registrado: derivar al Empleado Administrativo")
        self.assertFalse(ServicioRealizado.objects.exists())

    def test_empleado_sin_funcion_no_registra_servicio(self):
        usuario = crear_usuario("mecanico_sin_funcion", "MECANICO")
        crear_empleado(usuario, solicita_productos=True, ejecuta_servicios=False)
        self.client.force_login(usuario)
        respuesta = self.client.get(reverse("atencion:registrar"))
        self.assertEqual(respuesta.status_code, 403)
        self.assertTrue(RegistroAuditoria.objects.filter(operacion="ACCESO_DENEGADO", usuario=usuario).exists())
        # Tampoco sirve un ADMIN sin la función (la restricción vale para todos los perfiles).
        admin = crear_usuario("admin", "ADMIN")
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse("atencion:registrar")).status_code, 403)

    def test_administrativo_no_entra_a_atencion(self):
        self.client.force_login(crear_usuario("ana", "ADMINISTRATIVO"))
        self.assertEqual(self.client.get(reverse("atencion:inicio")).status_code, 403)
