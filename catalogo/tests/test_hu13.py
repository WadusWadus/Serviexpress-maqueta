"""HU13 · Productos · RF17 · CU08"""

from django.test import TestCase
from django.urls import reverse

from catalogo.forms import ServicioProductoForm
from catalogo.models import Producto
from core.tests.fabricas import crear_producto, crear_usuario


class ProductosTests(TestCase):
    def setUp(self):
        self.client.force_login(crear_usuario("administrativo", "ADMINISTRATIVO"))

    def test_codigo_duplicado_es_rechazado(self):
        crear_producto("ACE-10W40")
        for codigo in ["ACE-10W40", "ace-10w40"]:
            with self.subTest(codigo=codigo):
                respuesta = self.client.post(reverse("catalogo:producto_nuevo"),
                                             {"codigo": codigo, "descripcion": "Otro", "unidad": "LITRO", "activo": "on"})
                self.assertContains(respuesta, "Código: Ya existe un producto con ese código.")
        self.assertEqual(Producto.objects.count(), 1)

    def test_codigo_se_guarda_en_mayusculas(self):
        self.client.post(reverse("catalogo:producto_nuevo"),
                         {"codigo": "fil-ace", "descripcion": "Filtro", "unidad": "UNIDAD", "activo": "on"})
        self.assertTrue(Producto.objects.filter(codigo="FIL-ACE").exists())

    def test_producto_desactivado_no_aparece_en_selecciones(self):
        activo = crear_producto("ACTIVO")
        inactivo = crear_producto("INACTIVO")
        self.client.post(reverse("catalogo:producto_desactivar", args=[inactivo.pk]))
        inactivo.refresh_from_db()
        self.assertFalse(inactivo.activo)
        opciones = ServicioProductoForm().fields["producto"].queryset
        self.assertIn(activo, opciones)
        self.assertNotIn(inactivo, opciones)

    def test_mecanico_no_entra_al_catalogo(self):
        self.client.force_login(crear_usuario("mecanico", "MECANICO"))
        self.assertEqual(self.client.get(reverse("catalogo:productos")).status_code, 403)
