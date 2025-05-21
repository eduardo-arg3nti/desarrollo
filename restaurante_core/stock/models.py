from django.db import models
from django.core.exceptions import ValidationError

class Producto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    precio_costo = models.DecimalField(max_digits=10, decimal_places=2)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2)
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=0)
    categoria = models.CharField(max_length=50, blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.precio_costo < 0:
            raise ValidationError({'precio_costo': 'El precio de costo no puede ser negativo.'})
        if self.precio_venta < 0:
            raise ValidationError({'precio_venta': 'El precio de venta no puede ser negativo.'})
        if self.stock_actual < 0:
            raise ValidationError({'stock_actual': 'El stock actual no puede ser negativo.'})
        if self.stock_minimo < 0:
            raise ValidationError({'stock_minimo': 'El stock mínimo no puede ser negativo.'})

    def __str__(self):
        return self.nombre
