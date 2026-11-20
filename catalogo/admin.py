from django.contrib import admin

from .models import Producto, Servicio, ServicioProducto


class ServicioProductoInline(admin.TabularInline):
    model = ServicioProducto


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    inlines = [ServicioProductoInline]


admin.site.register(Producto)
