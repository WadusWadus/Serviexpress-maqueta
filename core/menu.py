"""Menú lateral. Cada entrada pertenece a un módulo de core.permisos.

Formato: (grupo, [(módulo, etiqueta, nombre_de_url), ...]). Las entradas de cada
módulo se agregan en el sprint que lo construye. Los íconos son de Bootstrap Icons.
"""

from django.urls import NoReverseMatch, reverse

MENU = [
    ("Administración", [
        ("usuarios", "Usuarios", "cuentas:usuarios"),
        ("personal", "Empleados", "personal:lista"),
        ("festivos", "Días festivos", "reservas:festivos"),
        ("auditoria", "Auditoría", "core:auditoria"),
    ]),
    ("Clientes", [
        ("clientes", "Fichas de clientes", "clientes:lista"),
        ("fiado", "Habilitar fiado", "clientes:fiado"),
    ]),
    ("Reservas", [
        ("reserva_web", "Reservar hora", "reservas:paso_servicio"),
        ("reserva_web", "Mis reservas", "reservas:mis_reservas"),
        ("agenda", "Agenda", "agenda:lista"),
        ("agenda", "Reservar en el local", "agenda:nueva"),
    ]),
    ("Atención", [
        ("atencion", "Reservas de hoy", "atencion:inicio"),
        ("atencion", "Cliente sin reserva", "atencion:registrar"),
        ("atencion", "Servicios realizados", "atencion:realizados"),
    ]),
    ("Ventas", [
        ("ventas", "Boletas", "ventas:boletas"),
        ("ventas", "Nueva boleta", "ventas:boleta_nueva"),
        ("ventas", "Facturas", "ventas:facturas"),
        ("ventas", "Nueva factura", "ventas:factura_nueva"),
    ]),
    ("Abastecimiento", [
        ("abastecimiento", "Proveedores", "abastecimiento:proveedores"),
        ("abastecimiento", "Órdenes de pedido", "abastecimiento:ordenes"),
        ("abastecimiento", "Nueva orden", "abastecimiento:orden_nueva"),
        ("abastecimiento", "Recepcionar", "abastecimiento:recepcion_nueva"),
        ("abastecimiento", "Recepciones", "abastecimiento:recepciones"),
    ]),
    ("Gestión", [
        ("informes", "Informes", "informes:inicio"),
        ("estadisticas_web", "Estadísticas web", "informes:estadisticas_web"),
    ]),
    ("Catálogo", [
        ("catalogo", "Servicios", "catalogo:servicios"),
        ("catalogo", "Productos", "catalogo:productos"),
    ]),
    ("Ayuda", [
        ("ayuda", "Manual de uso", "core:ayuda"),
    ]),
]

ICONOS = {
    "cuentas:usuarios": "shield-lock", "personal:lista": "person-badge", "reservas:festivos": "calendar-x",
    "core:auditoria": "journal-text", "clientes:lista": "people", "clientes:fiado": "wallet2",
    "reservas:paso_servicio": "calendar-plus", "reservas:mis_reservas": "calendar-check",
    "agenda:lista": "calendar2-week", "agenda:nueva": "calendar-plus", "atencion:inicio": "tools",
    "atencion:registrar": "clipboard-check", "atencion:realizados": "list-check", "ventas:boletas": "receipt",
    "ventas:boleta_nueva": "plus-lg", "ventas:facturas": "file-earmark-text", "ventas:factura_nueva": "plus-lg",
    "abastecimiento:proveedores": "building", "abastecimiento:ordenes": "cart-check",
    "abastecimiento:orden_nueva": "plus-lg", "abastecimiento:recepcion_nueva": "box-seam",
    "abastecimiento:recepciones": "boxes", "informes:inicio": "bar-chart", "informes:estadisticas_web": "graph-up",
    "catalogo:servicios": "wrench-adjustable", "catalogo:productos": "tag", "core:ayuda": "question-circle",
}

# Las acciones «Nueva …» se muestran dentro de cada pantalla; en el menú lateral solo van los destinos.
SOLO_ACCESO_DIRECTO = {"ventas:boleta_nueva", "ventas:factura_nueva", "abastecimiento:orden_nueva", "agenda:nueva"}


def menu_para(modulos, ruta_actual=""):
    """Filtra el menú dejando solo los módulos indicados; omite grupos vacíos y marca la entrada activa."""
    resultado, todas = [], []
    for grupo, entradas in MENU:
        visibles = []
        for modulo, etiqueta, nombre in entradas:
            if modulo not in modulos:
                continue
            try:
                url = reverse(nombre)
            except NoReverseMatch:
                continue
            entrada = {"modulo": modulo, "etiqueta": etiqueta, "url": nombre, "href": url,
                       "icono": ICONOS.get(nombre, "dot"), "lateral": nombre not in SOLO_ACCESO_DIRECTO, "activo": False}
            visibles.append(entrada)
            todas.append(entrada)
        if visibles:
            resultado.append({"grupo": grupo, "entradas": visibles,
                              "laterales": [e for e in visibles if e["lateral"]]})
    coincidencias = [e for e in todas if e["lateral"] and ruta_actual.startswith(e["href"])]
    if coincidencias:
        max(coincidencias, key=lambda e: len(e["href"]))["activo"] = True
    return resultado
