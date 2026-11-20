"""HU03 · RF04 · Ayuda contextual: averigua el módulo de la pantalla actual."""

from .models import SeccionAyuda

# Si la vista no declara su módulo (vistas sin @requiere_modulo), se usa el espacio de nombres de la URL.
MODULO_POR_NAMESPACE = {
    "cuentas": "usuarios", "personal": "personal", "clientes": "clientes", "catalogo": "catalogo",
    "agenda": "agenda", "atencion": "atencion", "ventas": "ventas", "abastecimiento": "abastecimiento",
    "informes": "informes",
}


def modulo_actual(request):
    coincidencia = getattr(request, "resolver_match", None)
    if coincidencia is None:
        return None
    vista = coincidencia.func
    modulo = getattr(vista, "modulo", None) or getattr(getattr(vista, "view_class", None), "modulo", None)
    return modulo or MODULO_POR_NAMESPACE.get(coincidencia.namespace)


def seccion_para(request):
    modulo = modulo_actual(request)
    if not modulo:
        return None
    return SeccionAyuda.objects.filter(modulo=modulo).first()
