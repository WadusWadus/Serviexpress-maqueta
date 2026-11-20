"""Datos demo · S2 · 10 productos y 5 servicios activos + 1 desactivado (sección 9)."""

from decimal import Decimal

from .models import Producto, Servicio, ServicioProducto

PRODUCTOS = [
    ("ACE-10W40", "Aceite 10W-40", "LITRO"),
    ("FIL-ACE", "Filtro de aceite", "UNIDAD"),
    ("FIL-AIR", "Filtro de aire", "UNIDAD"),
    ("PAS-FRE", "Pastillas de freno", "JUEGO"),
    ("LIQ-FRE", "Líquido de frenos", "LITRO"),
    ("REFRIG", "Refrigerante", "LITRO"),
    ("BUJIA", "Bujías", "UNIDAD"),
    ("AMPOLL", "Ampolleta", "UNIDAD"),
    ("ESCOB", "Escobillas", "JUEGO"),
    ("BATERIA", "Batería", "UNIDAD"),
]

# nombre, descripción, precio, activo, [(código, cantidad)]
SERVICIOS = [
    ("Cambio de aceite", "Cambio de aceite de motor y filtro.", 35000, True, [("ACE-10W40", "4"), ("FIL-ACE", "1")]),
    ("Cambio de pastillas", "Reemplazo de pastillas de freno delanteras.", 45000, True, [("PAS-FRE", "1")]),
    ("Revisión de frenos", "Revisión del sistema de frenos y nivel de líquido.", 20000, True, [("LIQ-FRE", "0.5")]),
    ("Cambio de batería", "Instalación de batería nueva y prueba de carga.", 15000, True, [("BATERIA", "1")]),
    ("Mantención básica", "Aceite, filtros y revisión general.", 60000, True,
     [("ACE-10W40", "4"), ("FIL-ACE", "1"), ("FIL-AIR", "1"), ("REFRIG", "1")]),
    ("Alineación (descontinuado)", "Servicio que el taller dejó de ofrecer.", 18000, False, []),
]


def cargar(salida):
    for codigo, descripcion, unidad in PRODUCTOS:
        Producto.objects.update_or_create(codigo=codigo, defaults={"descripcion": descripcion, "unidad": unidad, "activo": True})
    for nombre, descripcion, precio, activo, productos in SERVICIOS:
        servicio, _ = Servicio.objects.get_or_create(
            nombre=nombre, defaults={"descripcion": descripcion, "precio": precio, "activo": activo})
        for codigo, cantidad in productos:
            ServicioProducto.objects.get_or_create(servicio=servicio, producto=Producto.objects.get(codigo=codigo),
                                                   defaults={"cantidad": Decimal(cantidad)})
    salida.write("  catalogo: 10 productos, 6 servicios (1 desactivado)")
