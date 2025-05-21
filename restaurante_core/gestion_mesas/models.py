from django.db import models
# from ventas.models import Venta # Usar referencia como string 'ventas.Venta'

class Mesa(models.Model):
    ESTADOS_MESA = [
        ('disponible', 'Disponible'),
        ('ocupada', 'Ocupada'),
        ('reservada', 'Reservada'),
        # ('necesita_limpieza', 'Necesita Limpieza'), # Podría ser un estado futuro
    ]

    numero_mesa = models.CharField(
        max_length=10, # Ajustado a la especificación de la tarea
        unique=True, 
        help_text="Ej: 'Mesa 1', 'Barra 2'" # Ajustado a la especificación
    )
    capacidad = models.PositiveIntegerField(default=1)
    ubicacion = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text="Ej: 'Salón Principal', 'Terraza'" # Ajustado
    )
    estado = models.CharField(
        max_length=20, 
        choices=ESTADOS_MESA, 
        default='disponible'
    )
    
    venta_actual = models.ForeignKey(
        'ventas.Venta', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='mesa_asignada', # Como especificado en la tarea
        help_text="Venta activa asociada a esta mesa si está ocupada."
    )

    def __str__(self):
        return f"{self.numero_mesa} ({self.get_estado_display()})"

    class Meta:
        ordering = ['ubicacion', 'numero_mesa']
        verbose_name = "Mesa"
        verbose_name_plural = "Mesas"
