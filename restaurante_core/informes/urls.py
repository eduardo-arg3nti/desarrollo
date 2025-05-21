from django.urls import path
from .views import InformeProductosMasVendidosView

app_name = 'informes'

urlpatterns = [
    path('productos-mas-vendidos/', InformeProductosMasVendidosView.as_view(), name='productos_mas_vendidos'),
]
