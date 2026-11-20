from django import template

register = template.Library()


@register.filter
def pesos(valor):
    """12345 → '$12.345'."""
    if valor in (None, ""):
        return ""
    try:
        numero = int(round(float(valor)))
    except (TypeError, ValueError):
        return valor
    signo = "-" if numero < 0 else ""
    return f"{signo}${abs(numero):,}".replace(",", ".")


@register.filter
def cantidad(valor):
    """Decimal sin ceros sobrantes: 2.00 → '2', 1.50 → '1,5'."""
    if valor in (None, ""):
        return ""
    texto = f"{valor:f}".rstrip("0").rstrip(".") if "." in f"{valor}" else f"{valor}"
    return texto.replace(".", ",")


@register.simple_tag(takes_context=True)
def url_con(context, **cambios):
    """Querystring actual con los cambios indicados (para paginación con filtros)."""
    params = context["request"].GET.copy()
    for clave, valor in cambios.items():
        params[clave] = valor
    return "?" + params.urlencode()
