"""HU05 · Modificar y consultar ficha · RF06 · CU03 · RNF23"""

from django.test import TestCase
from django.urls import reverse

from core.tests.fabricas import crear_cliente, crear_usuario


class ModificarFichaTests(TestCase):
    def setUp(self):
        self.client.force_login(crear_usuario("administrativo", "ADMINISTRATIVO"))
        self.cliente = crear_cliente("cliente1", nombres="María", apellidos="González", telefono="111")

    def datos(self, **cambios):
        c = self.cliente
        return {"nombres": c.nombres, "apellidos": c.apellidos, "telefono": c.telefono, "email": "",
                "direccion": "", "version_leida": c.version} | cambios

    def test_modificacion_se_ve_en_la_ficha(self):
        url = reverse("clientes:editar", args=[self.cliente.pk])
        self.client.post(url, self.datos(telefono="+56 9 9999 0000"))
        ficha = self.client.get(reverse("clientes:ficha", args=[self.cliente.pk]))
        self.assertContains(ficha, "+56 9 9999 0000")
        busqueda = self.client.get(reverse("clientes:lista"), {"q": "cliente1"})
        self.assertContains(busqueda, "María González")

    def test_edicion_concurrente_avisa_conflicto(self):
        url = reverse("clientes:editar", args=[self.cliente.pk])
        datos_pestana_1 = self.datos(telefono="222")
        datos_pestana_2 = self.datos(telefono="333")  # ambas leyeron la misma versión
        self.client.post(url, datos_pestana_1)
        respuesta = self.client.post(url, datos_pestana_2)
        self.assertContains(respuesta, "Otro usuario modificó este registro mientras lo editaba")
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.telefono, "222")

    def test_lista_clientes_pagina_de_50(self):
        for i in range(59):
            crear_cliente(f"masivo{i}")
        respuesta = self.client.get(reverse("clientes:lista"))
        self.assertEqual(len(respuesta.context["page_obj"]), 50)
        self.assertEqual(len(self.client.get(reverse("clientes:lista"), {"page": 2}).context["page_obj"]), 10)

    def test_rut_no_se_edita(self):
        rut = self.cliente.rut
        self.client.post(reverse("clientes:editar", args=[self.cliente.pk]), self.datos(rut="11111111-1"))
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.rut, rut)
