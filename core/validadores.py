"""Validación del RUT chileno (módulo 11). La usan empleados, clientes y proveedores."""

import re

from django.core.exceptions import ValidationError


def digito_verificador(numero):
    """Devuelve el dígito verificador ('0'–'9' o 'K') del número de RUT."""
    suma, factor = 0, 2
    for cifra in reversed(str(numero)):
        suma += int(cifra) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - suma % 11
    return {11: "0", 10: "K"}.get(resto, str(resto))


def normalizar_rut(valor):
    """'12.345.678-k' → '12345678-K'. Devuelve el texto limpio sin validar el dígito."""
    limpio = re.sub(r"[^0-9kK]", "", str(valor or "")).upper()
    if len(limpio) < 2:
        return limpio
    return f"{limpio[:-1]}-{limpio[-1]}"


def validar_rut(valor):
    rut = normalizar_rut(valor)
    if not re.fullmatch(r"\d{1,8}-[\dK]", rut):
        raise ValidationError("RUT con formato inválido. Use el formato 12345678-9.", code="rut_formato")
    numero, dv = rut.split("-")
    if digito_verificador(numero) != dv:
        raise ValidationError("RUT inválido: el dígito verificador no corresponde.", code="rut_dv")


def rut_con_dv(numero):
    """Arma un RUT válido a partir del número (útil para datos de demostración y tests)."""
    return f"{numero}-{digito_verificador(numero)}"
