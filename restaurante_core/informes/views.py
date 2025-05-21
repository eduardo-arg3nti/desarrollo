from django.shortcuts import render
from django.views import View
from django.db.models import Sum, F, Value, CharField
from django.db.models.functions import Coalesce
from django.utils.timezone import make_aware, get_current_timezone
from datetime import datetime, time

from ventas.models import Venta, DetalleVenta
from stock.models import Producto
from .forms import DateRangeFilterForm

# Importar mixins de acceso desde una ubicación común si es necesario
# Asumiendo que los mixins están en 'restaurante_core.auth_mixins' o similar
# from restaurante_core.auth_mixins import AdministradorCajeroAccessMixin
# Por ahora, usaremos los helpers definidos en otras apps si están disponibles,
# o definiremos uno simple aquí.

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect

# Re-definiendo helpers aquí por simplicidad para este módulo.
# Idealmente, estarían en un archivo utils.py o auth_utils.py
def is_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

def es_administrador(user):
    return is_in_group(user, 'Administradores')

def es_cajero(user):
    return is_in_group(user, 'Cajeros')


class PersonalInformesAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin para restringir acceso a informes a Administradores o Cajeros."""
    def test_func(self):
        user = self.request.user
        return es_administrador(user) or es_cajero(user)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "Acceso denegado. Esta sección es para Administradores o Cajeros.")
        return redirect('home')


class InformeProductosMasVendidosView(PersonalInformesAccessMixin, View):
    template_name = 'informes/productos_mas_vendidos.html'
    form_class = DateRangeFilterForm

    def get(self, request, *args, **kwargs):
        form = self.form_class(request.GET or None)
        productos_vendidos = []

        fecha_desde_str = request.GET.get('fecha_desde')
        fecha_hasta_str = request.GET.get('fecha_hasta')

        # Estados de venta válidos para el informe
        estados_venta_validos = ['completado', 'entregado'] # 'completado' para mesa/mostrador, 'entregado' para delivery

        # Base queryset
        detalles_queryset = DetalleVenta.objects.filter(venta__estado_pedido__in=estados_venta_validos)

        if form.is_valid():
            fecha_desde = form.cleaned_data.get('fecha_desde')
            fecha_hasta = form.cleaned_data.get('fecha_hasta')

            if fecha_desde:
                # Convertir a datetime al inicio del día y hacerlo timezone-aware
                dt_desde = make_aware(datetime.combine(fecha_desde, time.min), get_current_timezone())
                detalles_queryset = detalles_queryset.filter(venta__fecha_hora__gte=dt_desde)
            
            if fecha_hasta:
                # Convertir a datetime al final del día y hacerlo timezone-aware
                dt_hasta = make_aware(datetime.combine(fecha_hasta, time.max), get_current_timezone())
                detalles_queryset = detalles_queryset.filter(venta__fecha_hora__lte=dt_hasta)

        # Si el formulario no es válido pero se intentó enviar (ej. fechas mal puestas en URL)
        # o si no hay fechas, se muestran todos los datos (o un rango por defecto si se prefiere)
        # Aquí, si no hay fechas o el form no es válido (por ej. GET inicial), se muestran todos.

        productos_vendidos = (
            detalles_queryset
            .values('producto__nombre') # Agrupar por nombre de producto
            .annotate(
                producto_id=F('producto__id'), # Para poder enlazar al producto si se quisiera
                total_cantidad_vendida=Sum('cantidad'),
                total_monto_generado=Sum(F('cantidad') * F('precio_unitario_venta'))
            )
            .order_by('-total_cantidad_vendida', '-total_monto_generado') # Ordenar
            .filter(total_cantidad_vendida__gt=0) # Solo mostrar si se vendió algo
        )
        
        # Convertir producto__nombre a nombre para la plantilla
        # y asegurar que los totales sean 0 si son None (Coalesce no es necesario si se filtra por __gt=0)
        # productos_vendidos = [
        #     {
        #         'nombre_producto': item['producto__nombre'], 
        #         'producto_id': item['producto_id'],
        #         'total_cantidad_vendida': item['total_cantidad_vendida'],
        #         'total_monto_generado': item['total_monto_generado']
        #     } for item in productos_vendidos_qs
        # ]


        context = {
            'form': form,
            'productos_vendidos': productos_vendidos,
            'fecha_desde': fecha_desde_str, # Para mantener en el template
            'fecha_hasta': fecha_hasta_str, # Para mantener en el template
        }
        return render(request, self.template_name, context)
