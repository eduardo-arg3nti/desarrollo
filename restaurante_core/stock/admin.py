from django.contrib import admin
from .models import Producto

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio_venta', 'stock_actual', 'activo', 'fecha_actualizacion')
    list_filter = ('activo', 'categoria')
    search_fields = ('nombre', 'descripcion', 'categoria')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    fieldsets = (
        (None, {
            'fields': ('nombre', 'descripcion', 'categoria', 'activo')
        }),
        ('Precios', {
            'fields': ('precio_costo', 'precio_venta')
        }),
        ('Stock', {
            'fields': ('stock_actual', 'stock_minimo')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        # Validaciones adicionales o lógica de negocio antes de guardar
        super().save_model(request, obj, form, change)
