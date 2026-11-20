"""HU12 · Catálogo de servicios con productos · RF15, RF16 · CU07"""

from django.test import TestCase
from django.urls import reverse

from catalogo.models import Servicio
from core.tests.fabricas import crear_producto, crear_servicio, crear_usuario


class ServiciosTests(TestCase):
    def setUp(self):
        self.client.force_login(crear_usuario("administrativo", "ADMINISTRATIVO"))
        self.aceite = crear_producto("ACE", descripcion="Aceite 10W-40", unidad="LITRO")
        self.filtro = crear_producto("FIL", descripcion="Filtro de aceite")

    def formset(self, filas):
        datos = {"productos-TOTAL_FORMS": str(len(filas)), "productos-INITIAL_FORMS": "0",
                 "productos-MIN_NUM_FORMS": "0", "productos-MAX_NUM_FORMS": "1000"}
        for i, (producto, cantidad) in enumerate(filas):
            datos[f"productos-{i}-producto"] = producto
            datos[f"productos-{i}-cantidad"] = cantidad
        return datos

    def test_crear_servicio_con_productos(self):
        datos = {"nombre": "Cambio de aceite", "descripcion": "", "precio": "35000", "duracion_bloques": "1",
                 "activo": "on"} | self.formset([(self.aceite.pk, "4"), (self.filtro.pk, "1"), ("", "")])
        self.client.post(reverse("catalogo:servicio_nuevo"), datos)
        servicio = Servicio.objects.get(nombre="Cambio de aceite")
        self.assertEqual(servicio.lineas_producto.count(), 2)

    def test_cantidad_cero_es_rechazada(self):
        datos = {"nombre": "X", "precio": "1000", "duracion_bloques": "1"} | self.formset([(self.aceite.pk, "0")])
        respuesta = self.client.post(reverse("catalogo:servicio_nuevo"), datos)
        self.assertContains(respuesta, "La cantidad debe ser mayor que 0")
        self.assertFalse(Servicio.objects.exists())

    def test_servicio_desactivado_no_aparece_en_reserva(self):
        activo = crear_servicio("Cambio de aceite")
        inactivo = crear_servicio("Mantención básica")
        self.client.post(reverse("catalogo:servicio_desactivar", args=[inactivo.pk]))
        self.assertIn(activo, Servicio.objects.reservables())
        self.assertNotIn(inactivo, Servicio.objects.reservables())

    def test_detalle_servicio_lista_productos(self):
        servicio = crear_servicio("Cambio de aceite")
        servicio.lineas_producto.create(producto=self.aceite, cantidad=4)
        servicio.lineas_producto.create(producto=self.filtro, cantidad=1)
        respuesta = self.client.get(reverse("catalogo:servicio_detalle", args=[servicio.pk]))
        self.assertContains(respuesta, "Aceite 10W-40")
        self.assertContains(respuesta, "Filtro de aceite")
