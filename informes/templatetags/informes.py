from django import template

from informes.consultas import formatear

register = template.Library()


@register.simple_tag
def celda(valor, formato):
    return formatear(valor, formato)


@register.filter
def zip_columnas(fila, columnas):
    return zip(fila, [formato for _, formato in columnas])
