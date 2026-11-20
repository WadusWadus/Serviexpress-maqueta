"""HU07 · Venta fiada y saldo · RF08, RF09 · CU14 (extiende CU12)"""

from django.urls import reverse

from clientes.models import MovimientoFiado
from core.tests.fabricas import crear_cliente, crear_realizado
from ventas import servicios as srv
from ventas.models import Boleta
from ventas.tests.base import VentasTestCase


class VentaFiadaTests(VentasTestCase):
    def setUp(self):
        super().setUp()
        self.cliente.fiado_habilitado = True
        self.cliente.save()
        self.url = f"{reverse('ventas:boleta_nueva')}?cliente={self.cliente.pk}"

    def test_boleta_fiada_suma_al_saldo(self):
        self.assertContains(self.client.get(self.url), "Venta fiada")
        self.client.post(self.url, {"servicios": [self.r1.pk, self.r2.pk], "fiada": "on"})
        boleta = Boleta.objects.get()
        self.assertTrue(boleta.fiada)
        self.assertEqual(self.cliente.saldo_fiado, 55000)
        saldo = self.client.get(reverse("clientes:saldo", args=[self.cliente.pk]))
        self.assertContains(saldo, "$55.000")

    def test_fiado_a_no_habilitado_es_rechazado(self):
        otro = crear_cliente("cliente2")
        realizado = crear_realizado(otro, self.aceite)
        url = f"{reverse('ventas:boleta_nueva')}?cliente={otro.pk}"
        self.assertNotContains(self.client.get(url), "Venta fiada")  # la casilla no aparece
        respuesta = self.client.post(url, {"servicios": [realizado.pk], "fiada": "on"})  # se fuerza
        self.assertContains(respuesta, "El cliente no está habilitado para comprar fiado")
        self.assertFalse(Boleta.objects.exists())
        self.assertFalse(MovimientoFiado.objects.exists())

    def test_anular_boleta_fiada_descuenta_saldo(self):
        boleta = srv.emitir_boleta(self.cliente, [self.r1], self.usuario, fiada=True)
        self.assertEqual(self.cliente.saldo_fiado, 35000)
        srv.anular_boleta(boleta, self.usuario, "Error")
        self.assertEqual(self.cliente.saldo_fiado, 0)
        self.assertEqual(MovimientoFiado.objects.count(), 2)

    def test_modificar_boleta_fiada_ajusta_saldo(self):
        boleta = srv.emitir_boleta(self.cliente, [self.r1, self.r2], self.usuario, fiada=True)
        linea = boleta.lineas.first()
        srv.modificar_boleta(boleta, self.usuario, "", {linea.pk: 30000})
        self.assertEqual(self.cliente.saldo_fiado, 50000)
        srv.anular_boleta(boleta, self.usuario, "Error")
        self.assertEqual(self.cliente.saldo_fiado, 0)

    def test_boleta_pagada_no_mueve_el_saldo(self):
        srv.emitir_boleta(self.cliente, [self.r1], self.usuario)
        self.assertEqual(self.cliente.saldo_fiado, 0)
