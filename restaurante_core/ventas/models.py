from django.db import models
from django.core.exceptions import ValidationError
# from stock.models import Producto # Using string reference 'stock.Producto'
# from gestion_mesas.models import Mesa # Using string reference 'gestion_mesas.Mesa'

class Venta(models.Model):
    TIPOS_VENTA = [
        ('mostrador', 'Mostrador'),
        ('mesa', 'Mesa'),
        ('delivery', 'Delivery'),
    ]
    ESTADOS_PEDIDO = [
        ('pendiente', 'Pendiente'),          # Pedido recién creado, esperando confirmación
        ('confirmado', 'Confirmado'),        # Pedido aceptado por el restaurante
        ('en_preparacion', 'En preparación'),  # Cocinando
        ('listo_para_despacho', 'Listo para Despacho'), # Listo para que el repartidor recoja
        ('en_camino', 'En Camino'),          # El repartidor está en ruta
        ('entregado', 'Entregado'),          # Cliente recibió el pedido (finalizado para delivery)
        ('cancelado', 'Cancelado'),          # Pedido cancelado
    ]

    fecha_hora = models.DateTimeField(auto_now_add=True)
    tipo_venta = models.CharField(max_length=20, choices=TIPOS_VENTA)
    total_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    estado_pedido = models.CharField(max_length=20, choices=ESTADOS_PEDIDO, default='pendiente')
    
    # ForeignKey al modelo Mesa en la app gestion_mesas.
    mesa = models.ForeignKey(
        'gestion_mesas.Mesa', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='ventas_asociadas' # Actualizado según la tarea
    )
    
    cliente_nombre = models.CharField(max_length=100, blank=True, null=True)
    cliente_direccion = models.CharField(max_length=200, blank=True, null=True)
    cliente_telefono = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Venta #{self.pk} - {self.tipo_venta} - {self.fecha_hora.strftime('%Y-%m-%d %H:%M')}"

    def clean(self):
        if self.total_venta < 0:
            raise ValidationError({'total_venta': 'El total de la venta no puede ser negativo.'})
        # Validaciones adicionales para tipo_venta y mesa/cliente podrían ir aquí o en forms/views.
        # Ejemplo: if self.tipo_venta == 'mesa' and not self.mesa_id:
        # raise ValidationError({'mesa': 'Se requiere una mesa para ventas de tipo "Mesa".'})
        # Ejemplo: if self.tipo_venta == 'delivery' and not self.cliente_direccion:
        # raise ValidationError({'cliente_direccion': 'Se requiere dirección para ventas de tipo "Delivery".'})


    def actualizar_total(self):
        """
        Calcula y actualiza el total_venta basado en los detalles.
        Se llama desde DetalleVenta.save() y DetalleVenta.delete()
        """
        # Usamos self.detalles.aggregate para mayor eficiencia en DB
        from django.db.models import Sum
        nuevo_total = self.detalles.aggregate(total=Sum('subtotal'))['total'] or 0.00
        if self.total_venta != nuevo_total:
            self.total_venta = nuevo_total
            self.save(update_fields=['total_venta'])

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    # Usamos string reference para Producto para evitar import directo aquí
    producto = models.ForeignKey('stock.Producto', on_delete=models.PROTECT) 
    cantidad = models.PositiveIntegerField()
    precio_unitario_venta = models.DecimalField(max_digits=10, decimal_places=2) # Precio en el momento de la venta
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, editable=False) # Calculado, no editable directamente

    def __str__(self):
        # Es mejor acceder al nombre del producto de forma segura, podría no estar cargado completamente
        # o el producto podría ser eliminado (aunque PROTECT lo previene).
        producto_nombre = self.producto.nombre if self.producto else "Producto no disponible"
        return f"{self.cantidad} x {producto_nombre} @ ${self.precio_unitario_venta}"

    def clean(self):
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor que cero.'})
        if self.precio_unitario_venta < 0:
            raise ValidationError({'precio_unitario_venta': 'El precio unitario no puede ser negativo.'})
        # Asegurarse que hay stock suficiente antes de confirmar la venta (esto iría en la lógica de negocio/forms)
        # if self.producto and self.cantidad > self.producto.stock_actual:
        #     raise ValidationError({'cantidad': f"Stock insuficiente para {self.producto.nombre}. Disponible: {self.producto.stock_actual}"})


    def save(self, *args, **kwargs):
        # Calcular subtotal antes de guardar
        self.subtotal = self.cantidad * self.precio_unitario_venta
        super().save(*args, **kwargs)
        # No es necesario llamar a self.venta.actualizar_total() aquí si la señal lo maneja,
        # pero si no se usan señales, esta es la forma directa.
        # Para evitar recursión si save() de Venta llamara a save() de DetalleVenta de alguna forma:
        if kwargs.get('_from_venta_save', False): # Evitar bucle si Venta.save() modificara detalles
            pass
        else:
            self.venta.actualizar_total()


    def delete(self, *args, **kwargs):
        venta_asociada = self.venta
        super().delete(*args, **kwargs)
        venta_asociada.actualizar_total()
