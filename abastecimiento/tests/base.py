from decimal import Decimal

from django.test import TestCase

from core.tests.fabricas import crear_empleado, crear_producto, crear_proveedor, crear_usuario


class AbastecimientoTestCase(TestCase):
    def setUp(self):
        self.usuario = crear_usuario("administrativo", "ADMINISTRATIVO")
        self.empleado = crear_empleado(self.usuario, solicita_productos=True, ejecuta_servicios=False)
        self.no_habilitado = crear_usuario("administrativo2", "ADMINISTRATIVO")
        crear_empleado(self.no_habilitado, solicita_productos=False, ejecuta_servicios=True)
        self.proveedor = crear_proveedor("Lubricantes del Sur")
        self.aceite = crear_producto("ACE-10W40", descripcion="Aceite 10W-40")
        self.filtro = crear_producto("FIL-ACE", descripcion="Filtro de aceite")
        self.bateria = crear_producto("BATERIA", descripcion="Batería")
        self.client.force_login(self.usuario)

    @staticmethod
    def formset(filas, prefijo="lineas", extra=0):
        datos = {f"{prefijo}-TOTAL_FORMS": str(len(filas) + extra), f"{prefijo}-INITIAL_FORMS": "0",
                 f"{prefijo}-MIN_NUM_FORMS": "0", f"{prefijo}-MAX_NUM_FORMS": "1000"}
        for i, (producto, cantidad) in enumerate(filas):
            datos[f"{prefijo}-{i}-producto"] = producto.pk
            datos[f"{prefijo}-{i}-cantidad"] = str(cantidad)
        return datos

    def crear_orden(self, filas=None):
        from abastecimiento import servicios as srv

        filas = filas or [(self.aceite, Decimal("10")), (self.filtro, Decimal("5"))]
        return srv.crear_orden(self.empleado, self.usuario, self.proveedor, filas)
