from django.urls import path
from .views import (
    VentaMostradorView, 
    VentaMostradorConfirmacionView,
    GestionDeliveryView,
    ListaPedidosDeliveryView,
    ImprimirComandaView
)

app_name = 'ventas'

urlpatterns = [
    path('mostrador/', VentaMostradorView.as_view(), name='venta_mostrador'),
    # Las acciones del carrito (add, update, remove, clear, register_sale) son manejadas
    # por el método POST de VentaMostradorView, diferenciadas por un campo 'action'.
    # No se necesitan URLs separadas para cada acción del carrito si se sigue este enfoque.    
    path('mostrador/confirmacion/<int:venta_id>/', VentaMostradorConfirmacionView.as_view(), name='venta_mostrador_confirmacion'),

    # URLs para Gestión de Delivery
    path('delivery/nuevo/', GestionDeliveryView.as_view(), name='gestion_delivery'),
    # Las acciones del carrito de delivery y el registro del pedido son manejadas por POST en GestionDeliveryView.
    path('delivery/pedidos/', ListaPedidosDeliveryView.as_view(), name='lista_pedidos_delivery'),
    # La acción de cambiar estado de pedido es manejada por POST en ListaPedidosDeliveryView.

    # URL para Imprimir Comanda
    path('venta/<int:venta_id>/comanda/imprimir/', ImprimirComandaView.as_view(), name='imprimir_comanda'),
]
