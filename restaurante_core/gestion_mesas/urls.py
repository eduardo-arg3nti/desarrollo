from django.urls import path
from .views import TableroMesasView, GestionPedidoMesaView

app_name = 'gestion_mesas'

urlpatterns = [
    path('', TableroMesasView.as_view(), name='tablero_mesas'),
    path('mesa/<int:mesa_id>/gestionar/', GestionPedidoMesaView.as_view(), name='gestionar_pedido_mesa'),
]
