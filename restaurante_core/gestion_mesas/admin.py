from django.contrib import admin
from .models import Mesa

@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display = ('numero_mesa', 'capacidad', 'estado', 'ubicacion', 'venta_actual_info')
    list_filter = ('estado', 'ubicacion', 'capacidad')
    search_fields = ('numero_mesa', 'ubicacion')
    # raw_id_fields = ('venta_actual',) # Si hay muchas ventas, mejora performance

    fieldsets = (
        (None, {
            'fields': ('numero_mesa', 'capacidad', 'ubicacion', 'estado')
        }),
        ('Gestión de Venta (Avanzado)', {
            'classes': ('collapse',), # Colapsado por defecto
            'fields': ('venta_actual',)
        }),
    )

    @admin.display(description='Venta Actual ID', ordering='venta_actual__pk')
    def venta_actual_info(self, obj):
        if obj.venta_actual:
            # Crear un enlace al admin de la venta actual si es posible
            from django.urls import reverse
            from django.utils.html import format_html
            link = reverse(f"admin:{obj.venta_actual._meta.app_label}_{obj.venta_actual._meta.model_name}_change", args=[obj.venta_actual.pk])
            return format_html('Venta <a href="{}">#{}</a>', link, obj.venta_actual.pk)
        return "N/A"
    
    # Acciones personalizadas
    def make_disponible(modeladmin, request, queryset):
        # Primero, asegurarse de que no haya una venta activa asignada si se va a marcar como disponible
        # Esto es una simplificación, una lógica más robusta podría requerir cerrar/cancelar la venta_actual
        for mesa in queryset.filter(estado='ocupada'):
            if mesa.venta_actual:
                # Aquí se podría añadir lógica para cambiar el estado de la venta_actual a 'cancelado' o 'completado'
                # por ahora, solo desasociamos.
                # mesa.venta_actual.estado_pedido = 'cancelado' # Ejemplo
                # mesa.venta_actual.save()
                pass # No se modifica la venta, solo se desasocia la mesa
        
        queryset.update(estado='disponible', venta_actual=None)
    make_disponible.short_description = "Marcar seleccionadas como Disponibles (y desasociar venta)"

    def make_reservada(modeladmin, request, queryset):
        queryset.update(estado='reservada')
    make_reservada.short_description = "Marcar seleccionadas como Reservadas"

    actions = [make_disponible, make_reservada]
