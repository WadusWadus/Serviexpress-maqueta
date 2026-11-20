"""HU23 · Exportar informes · RF32 · CU15"""

import io
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from docx import Document
from openpyxl import load_workbook

from core.tests.fabricas import crear_cliente, crear_empleado, crear_realizado, crear_servicio, crear_usuario
from informes.consultas import formatear


class ExportarTests(TestCase):
    def setUp(self):
        self.client.force_login(crear_usuario("admin", "ADMIN"))
        hoy = timezone.localdate()
        mecanico = crear_empleado(crear_usuario("mec", "MECANICO"), nombres="Carlos", apellidos="Muñoz")
        for i, nombre in enumerate(["Ana", "Pedro", "Lucía"]):
            crear_realizado(crear_cliente(nombre.lower(), nombres=nombre), crear_servicio(f"Servicio {i}", 1000 * (i + 1)),
                            mecanico, fecha=hoy - timedelta(days=i))
        self.url = reverse("informes:informe", args=["servicios"])
        self.pantalla = self.client.get(self.url).context["informe"]

    def texto_esperado(self):
        return [[formatear(v, f) for v, (_, f) in zip(fila, self.pantalla.columnas)] for fila in self.pantalla.filas]

    def exportar(self, formato):
        respuesta = self.client.get(self.url, {"formato": formato})
        self.assertEqual(respuesta.status_code, 200)
        nombre = f"informe-servicios-{self.pantalla.desde:%Y-%m-%d}-{self.pantalla.hasta:%Y-%m-%d}.{formato}"
        self.assertIn(nombre, respuesta["Content-Disposition"])
        return respuesta.content

    def test_exportacion_txt_mismas_filas(self):
        lineas = self.exportar("txt").decode("utf-8").splitlines()
        self.assertEqual(lineas[0].split("\t"), [c for c, _ in self.pantalla.columnas])
        self.assertEqual([l.split("\t") for l in lineas[1:]], self.texto_esperado())

    def test_exportacion_xlsx_mismas_filas(self):
        hoja = load_workbook(io.BytesIO(self.exportar("xlsx"))).active
        filas = list(hoja.iter_rows(values_only=True))
        self.assertEqual(list(filas[0]), [c for c, _ in self.pantalla.columnas])
        self.assertTrue(hoja["A1"].font.bold)
        self.assertEqual(len(filas) - 1, len(self.pantalla.filas))
        for exportada, original in zip(filas[1:], self.pantalla.filas):
            self.assertEqual(exportada[0].date(), original[0])  # fecha
            self.assertEqual(list(exportada[1:]), original[1:])

    def test_exportacion_docx_mismas_filas(self):
        tabla = Document(io.BytesIO(self.exportar("docx"))).tables[0]
        filas = [[c.text for c in fila.cells] for fila in tabla.rows]
        self.assertEqual(filas[0], [c for c, _ in self.pantalla.columnas])
        self.assertEqual(filas[1:], self.texto_esperado())

    def test_exportacion_no_incluye_contrasenas(self):
        for formato in ("txt", "docx"):
            self.assertNotIn(b"pbkdf2", self.exportar(formato))
