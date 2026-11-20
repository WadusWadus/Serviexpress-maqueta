from django.contrib import admin

from .models import LineaOrden, OrdenPedido, Proveedor, Recepcion


class LineaOrdenInline(admin.TabularInline):
    model = LineaOrden


@admin.register(OrdenPedido)
class OrdenPedidoAdmin(admin.ModelAdmin):
    list_display = ["numero", "proveedor", "fecha", "creada_por"]
    inlines = [LineaOrdenInline]


admin.site.register(Proveedor)
admin.site.register(Recepcion)
