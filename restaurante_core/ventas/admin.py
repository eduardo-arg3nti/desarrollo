from django.contrib import admin
from .models import Venta, DetalleVenta
# from stock.models import Producto # Para el formfield_for_foreignkey si se usa

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    fields = ('producto', 'cantidad', 'precio_unitario_venta', 'subtotal')
    readonly_fields = ('subtotal',)
    extra = 1
    # raw_id_fields = ('producto',) # Descomentar si la lista de productos es muy larga

    # Opcional: Personalizar el queryset para el campo 'producto' en el inline
    # def formfield_for_foreignkey(self, db_field, request, **kwargs):
    #     if db_field.name == "producto":
    #         kwargs["queryset"] = Producto.objects.filter(activo=True).order_by('nombre')
    #     return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_hora', 'tipo_venta', 'total_venta', 'estado_pedido', 'mesa_display', 'cliente_nombre')
    list_filter = ('tipo_venta', 'estado_pedido', 'fecha_hora', 'mesa')
    search_fields = ('id', 'cliente_nombre', 'cliente_direccion', 'cliente_telefono', 'mesa__numero_mesa') # Usar numero_mesa de Mesa
    readonly_fields = ('fecha_hora', 'total_venta') 
    inlines = [DetalleVentaInline]
    raw_id_fields = ('mesa',) # Para mejor rendimiento si hay muchas mesas
    
    fieldsets = (
        (None, {
            'fields': ('tipo_venta', 'estado_pedido', 'total_venta', 'fecha_hora')
        }),
        ('Información de Mesa (si aplica)', {
            'classes': ('collapse',),
            'fields': ('mesa',) 
        }),
        ('Información de Cliente (si aplica)', {
            'classes': ('collapse',),
            'fields': ('cliente_nombre', 'cliente_direccion', 'cliente_telefono')
        }),
    )

    @admin.display(description='Mesa Asignada', ordering='mesa__numero_mesa')
    def mesa_display(self, obj):
        if obj.mesa:
            from django.urls import reverse
            from django.utils.html import format_html
            link = reverse(f"admin:{obj.mesa._meta.app_label}_{obj.mesa._meta.model_name}_change", args=[obj.mesa.pk])
            return format_html('<a href="{}">{}</a>', link, obj.mesa.numero_mesa)
        return "N/A"

    # No es estrictamente necesario sobreescribir save_model solo para actualizar total si save_related ya lo hace.
    # def save_model(self, request, obj, form, change):
    #     super().save_model(request, obj, form, change)
    #     # obj.actualizar_total() # Se llama en save_related que es más apropiado para inlines

    def save_related(self, request, form, formsets, change):
        """
        Se llama después de que todos los formsets (inlines) han sido guardados.
        Ideal para actualizar el total de la venta.
        """
        super().save_related(request, form, formsets, change)
        form.instance.actualizar_total()

@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'venta_link', 'producto_link', 'cantidad', 'precio_unitario_venta', 'subtotal')
    list_select_related = ('venta', 'producto') # Optimiza la carga de datos relacionados
    search_fields = ('venta__id', 'producto__nombre', 'venta__cliente_nombre')
    readonly_fields = ('subtotal',)
    # raw_id_fields = ('producto', 'venta') # Útil para grandes cantidades de datos

    @admin.display(description='Venta ID', ordering='venta__id')
    def venta_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        link = reverse(f"admin:{obj.venta._meta.app_label}_{obj.venta._meta.model_name}_change", args=[obj.venta.pk])
        return format_html('<a href="{}">{}</a>', link, obj.venta.pk)

    @admin.display(description='Producto', ordering='producto__nombre')
    def producto_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.producto:
            link = reverse(f"admin:{obj.producto._meta.app_label}_{obj.producto._meta.model_name}_change", args=[obj.producto.pk])
            return format_html('<a href="{}">{}</a>', link, obj.producto.nombre)
        return "N/A"
    
    # Los métodos save_model, delete_model y delete_queryset para DetalleVenta
    # no son necesarios si la lógica de actualizar_total está bien implementada
    # en DetalleVenta.save/delete y VentaAdmin.save_related.
    # Si se quisiera doble-chequear o forzar:
    # def save_model(self, request, obj, form, change):
    #     super().save_model(request, obj, form, change)
    #     obj.venta.actualizar_total()
        
    # def delete_model(self, request, obj):
    #     venta_asociada = obj.venta
    #     super().delete_model(request, obj)
    #     venta_asociada.actualizar_total()

    # def delete_queryset(self, request, queryset):
    #     ventas_afectadas = {obj.venta for obj in queryset} # Colecciona las ventas únicas
    #     super().delete_queryset(request, queryset)
    #     for venta in ventas_afectadas:
    #         venta.actualizar_total()
