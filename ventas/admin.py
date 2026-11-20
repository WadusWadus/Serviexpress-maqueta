from django.contrib import admin

from .models import Boleta, Factura, LineaBoleta, LineaFactura


class LineaBoletaInline(admin.TabularInline):
    model = LineaBoleta
    can_delete = False


@admin.register(Boleta)
class BoletaAdmin(admin.ModelAdmin):
    """RNF09 · Ni siquiera desde el admin se puede eliminar una boleta."""

    list_display = ["numero", "cliente", "fecha_emision", "total", "estado"]
    inlines = [LineaBoletaInline]

    def has_delete_permission(self, request, obj=None):
        return False


class LineaFacturaInline(admin.TabularInline):
    model = LineaFactura
    can_delete = False


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ["numero", "cliente", "fecha", "total"]
    inlines = [LineaFacturaInline]

    def has_delete_permission(self, request, obj=None):
        return False
