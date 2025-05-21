from django.urls import path
from .views import (
    ProductoListView,
    ProductoCreateView,
    ProductoUpdateView,
    producto_delete_logico
)

app_name = 'stock'

urlpatterns = [
    path('', ProductoListView.as_view(), name='producto_list'),
    path('nuevo/', ProductoCreateView.as_view(), name='producto_create'),
    path('editar/<int:pk>/', ProductoUpdateView.as_view(), name='producto_update'),
    path('eliminar/<int:pk>/', producto_delete_logico, name='producto_delete'),
]
