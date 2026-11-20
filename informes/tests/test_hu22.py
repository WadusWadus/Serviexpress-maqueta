"""HU22 · Informes con filtros, vista previa e impresión · RF30, RF31 · RNF03 · CU15"""

import time as reloj
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from abastecimiento import servicios as srv_abast
from core.tests.fabricas import (crear_cliente, crear_empleado, crear_producto, crear_proveedor, crear_realizado,
                                 crear_servicio, crear_usuario)
from reservas.models import ServicioRealizado


class InformesTests(TestCase):
    def setUp(self):
        self.admin = crear_usuario("admin", "ADMIN")
        self.client.force_login(self.admin)
        self.hoy = timezone.localdate()
        self.ana, self.pedro = crear_cliente("ana", nombres="Ana"), crear_cliente("pedro", nombres="Pedro")
        self.aceite, self.frenos = crear_servicio("Cambio de aceite"), crear_servicio("Revisión de frenos")
        self.mec1 = crear_empleado(crear_usuario("mec1", "MECANICO"), nombres="Carlos", apellidos="Muñoz")
        self.mec2 = crear_empleado(crear_usuario("mec2", "MECANICO"), nombres="Diego", apellidos="Paredes")
        crear_realizado(self.ana, self.aceite, self.mec1, fecha=self.hoy)
        crear_realizado(self.pedro, self.frenos, self.mec2, fecha=self.hoy - timedelta(days=3))
        crear_realizado(self.pedro, self.aceite, self.mec1, fecha=self.hoy - timedelta(days=50))  # fuera del rango por defecto

    def filas(self, tipo, **filtros):
        respuesta = self.client.get(reverse("informes:informe", args=[tipo]), filtros)
        self.assertEqual(respuesta.status_code, 200)
        return respuesta.context["informe"].filas

    def test_filtro_fecha(self):
        self.assertEqual(len(self.filas("servicios")), 2)  # últimos 30 días por defecto
        desde = (self.hoy - timedelta(days=60)).isoformat()
        self.assertEqual(len(self.filas("servicios", desde=desde, hasta=self.hoy.isoformat())), 3)
        self.assertEqual(len(self.filas("servicios", desde=self.hoy.isoformat(), hasta=self.hoy.isoformat())), 1)

    def test_filtro_cliente(self):
        filas = self.filas("servicios", cliente=self.pedro.pk)
        self.assertEqual([f[1] for f in filas], [self.pedro.nombre_completo])

    def test_filtro_servicio(self):
        filas = self.filas("servicios", servicio=self.frenos.pk)
        self.assertEqual([f[2] for f in filas], ["Revisión de frenos"])

    def test_filtro_empleado(self):
        filas = self.filas("servicios", empleado=self.mec2.pk)
        self.assertEqual([f[3] for f in filas], ["Diego Paredes"])

    def test_filtro_proveedor(self):
        usuario = crear_usuario("administrativo", "ADMINISTRATIVO")
        empleado = crear_empleado(usuario, solicita_productos=True)
        lubri, frenos = crear_proveedor("Lubricantes"), crear_proveedor("Frenos Chile")
        producto = crear_producto("ACE")
        srv_abast.crear_orden(empleado, usuario, lubri, [(producto, Decimal("5"))])
        srv_abast.crear_orden(empleado, usuario, frenos, [(producto, Decimal("2"))])
        filas = self.filas("abastecimiento", proveedor=frenos.pk)
        self.assertEqual([(f[2], f[4]) for f in filas], [("Frenos Chile", Decimal("2"))])

    def test_vista_impresion_sin_menu(self):
        en_pantalla = self.client.get(reverse("informes:informe", args=["servicios"]))
        self.assertContains(en_pantalla, 'id="menu-perfil"')
        self.assertContains(en_pantalla, "imprimir=1")
        impresion = self.client.get(reverse("informes:informe", args=["servicios"]), {"imprimir": "1"})
        self.assertNotContains(impresion, 'id="menu-perfil"')
        self.assertNotContains(impresion, "navbar")
        self.assertContains(impresion, "window.print()")
        self.assertContains(impresion, "Ana")

    def test_informe_pequeno_menos_de_5_segundos(self):
        """RNF03 · Evidencia en local (no es medición del VPS)."""
        ServicioRealizado.objects.bulk_create([
            ServicioRealizado(cliente=self.ana, servicio=self.aceite, empleado=self.mec1, fecha=self.hoy - timedelta(days=i % 30))
            for i in range(998)
        ])
        inicio = reloj.perf_counter()
        respuesta = self.client.get(reverse("informes:informe", args=["servicios"]))
        duracion = reloj.perf_counter() - inicio
        self.assertEqual(len(respuesta.context["informe"].filas), 1000)
        self.assertFalse(respuesta.context["informe"].grande)
        self.assertNotContains(respuesta, "Informe grande")
        self.assertLess(duracion, 5)

    def test_informe_grande_muestra_aviso(self):
        desde = (self.hoy - timedelta(days=60)).isoformat()
        respuesta = self.client.get(reverse("informes:informe", args=["servicios"]), {"desde": desde, "hasta": self.hoy.isoformat()})
        self.assertContains(respuesta, "Informe grande: el tiempo de respuesta no está comprometido")
        self.assertContains(respuesta, 'id="indicador-carga"')

    def test_todos_los_tipos_se_generan(self):
        for tipo in ["servicios", "ventas", "reservas", "abastecimiento"]:
            with self.subTest(tipo=tipo):
                self.assertEqual(self.client.get(reverse("informes:informe", args=[tipo])).status_code, 200)
        self.assertEqual(self.client.get(reverse("informes:informe", args=["otro"])).status_code, 404)

    def test_mecanico_no_ve_informes(self):
        self.client.force_login(crear_usuario("mecanico", "MECANICO"))
        self.assertEqual(self.client.get(reverse("informes:inicio")).status_code, 403)
