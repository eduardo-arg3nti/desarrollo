from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.utils.timezone import make_aware, get_current_timezone
from datetime import datetime, timedelta, time

from stock.models import Producto
from ventas.models import Venta, DetalleVenta
from decimal import Decimal

class InformesIntegrationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Crear grupos
        cls.admin_group, _ = Group.objects.get_or_create(name='Administradores')
        cls.cajero_group, _ = Group.objects.get_or_create(name='Cajeros')

        # Crear usuarios
        cls.admin_user = User.objects.create_user(username='testadmininformes', password='testpassword123', is_staff=True)
        cls.admin_user.groups.add(cls.admin_group)

        cls.cajero_user = User.objects.create_user(username='testcajeroinformes', password='testpassword123')
        cls.cajero_user.groups.add(cls.cajero_group)

        # Crear productos
        cls.producto_a = Producto.objects.create(nombre='Producto A Informes', precio_venta=Decimal('10.00'), stock_actual=100)
        cls.producto_b = Producto.objects.create(nombre='Producto B Informes', precio_venta=Decimal('20.00'), stock_actual=100)
        cls.producto_c = Producto.objects.create(nombre='Producto C Informes', precio_venta=Decimal('5.00'), stock_actual=100)

        # Crear ventas en diferentes fechas y con diferentes estados
        tz = get_current_timezone() # Usar timezone actual del proyecto

        # Venta 1 (Ayer) - completada
        # Usar datetime.combine con time.min/max para asegurar que la fecha completa está dentro del rango
        ayer = datetime.now().date() - timedelta(days=1)
        venta1_dt = make_aware(datetime.combine(ayer, time(10, 0, 0)), timezone=tz) # Ayer a las 10:00
        venta1 = Venta.objects.create(tipo_venta='mostrador', estado_pedido='completado', fecha_hora=venta1_dt)
        DetalleVenta.objects.create(venta=venta1, producto=cls.producto_a, cantidad=5, precio_unitario_venta=cls.producto_a.precio_venta) # 50
        DetalleVenta.objects.create(venta=venta1, producto=cls.producto_b, cantidad=2, precio_unitario_venta=cls.producto_b.precio_venta) # 40

        # Venta 2 (Hoy) - entregado (delivery)
        hoy = datetime.now().date()
        venta2_dt = make_aware(datetime.combine(hoy, time(12,0,0)), timezone=tz) # Hoy a las 12:00
        venta2 = Venta.objects.create(tipo_venta='delivery', estado_pedido='entregado', fecha_hora=venta2_dt)
        DetalleVenta.objects.create(venta=venta2, producto=cls.producto_a, cantidad=10, precio_unitario_venta=cls.producto_a.precio_venta) # 100
        DetalleVenta.objects.create(venta=venta2, producto=cls.producto_c, cantidad=3, precio_unitario_venta=cls.producto_c.precio_venta)   # 15

        # Venta 3 (Hoy) - en_preparacion (no debe contar para productos más vendidos)
        venta3_dt = make_aware(datetime.combine(hoy, time(13,0,0)), timezone=tz) # Hoy a las 13:00
        venta3 = Venta.objects.create(tipo_venta='mesa', estado_pedido='en_preparacion', fecha_hora=venta3_dt)
        DetalleVenta.objects.create(venta=venta3, producto=cls.producto_b, cantidad=5, precio_unitario_venta=cls.producto_b.precio_venta)

        # Venta 4 (Hace 2 días) - completada
        hace_dos_dias = datetime.now().date() - timedelta(days=2)
        venta4_dt = make_aware(datetime.combine(hace_dos_dias, time(14,0,0)), timezone=tz) # Hace 2 días a las 14:00
        venta4 = Venta.objects.create(tipo_venta='mostrador', estado_pedido='completado', fecha_hora=venta4_dt)
        DetalleVenta.objects.create(venta=venta4, producto=cls.producto_b, cantidad=3, precio_unitario_venta=cls.producto_b.precio_venta) # 60

        cls.client = Client()

    def setUp(self):
        self.client.login(username='testcajeroinformes', password='testpassword123')

    def test_informe_productos_mas_vendidos_sin_filtro(self):
        """
        Test del informe de productos más vendidos sin filtros de fecha.
        Verifica el orden y las cantidades/montos totales.
        """
        url_informe = reverse('informes:productos_mas_vendidos')
        response = self.client.get(url_informe)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'informes/productos_mas_vendidos.html')
        
        productos_vendidos_context = response.context.get('productos_vendidos')
        self.assertIsNotNone(productos_vendidos_context, "El contexto no contiene 'productos_vendidos'.")
        self.assertEqual(len(productos_vendidos_context), 3, "Deberían listarse 3 productos diferentes.")

        # Producto A: 5 (venta1) + 10 (venta2) = 15 unidades. Monto: (5*10) + (10*10) = 50 + 100 = 150
        # Producto B: 2 (venta1) + 3 (venta4) = 5 unidades. Monto: (2*20) + (3*20) = 40 + 60 = 100
        # Producto C: 3 (venta2) = 3 unidades. Monto: (3*5) = 15
        
        # Orden esperado: A (15), B (5), C (3)
        self.assertEqual(productos_vendidos_context[0]['producto__nombre'], self.producto_a.nombre)
        self.assertEqual(productos_vendidos_context[0]['total_cantidad_vendida'], 15)
        self.assertEqual(productos_vendidos_context[0]['total_monto_generado'], Decimal('150.00'))

        self.assertEqual(productos_vendidos_context[1]['producto__nombre'], self.producto_b.nombre)
        self.assertEqual(productos_vendidos_context[1]['total_cantidad_vendida'], 5)
        self.assertEqual(productos_vendidos_context[1]['total_monto_generado'], Decimal('100.00'))

        self.assertEqual(productos_vendidos_context[2]['producto__nombre'], self.producto_c.nombre)
        self.assertEqual(productos_vendidos_context[2]['total_cantidad_vendida'], 3)
        self.assertEqual(productos_vendidos_context[2]['total_monto_generado'], Decimal('15.00'))


    def test_informe_productos_mas_vendidos_filtro_fecha_hoy(self):
        """Test del informe filtrando solo para ventas de hoy."""
        url_informe = reverse('informes:productos_mas_vendidos')
        fecha_hoy_str = datetime.now().date().strftime('%Y-%m-%d')
        
        response = self.client.get(url_informe, {'fecha_desde': fecha_hoy_str, 'fecha_hasta': fecha_hoy_str})
        self.assertEqual(response.status_code, 200)
        
        productos_vendidos_context = response.context.get('productos_vendidos')
        self.assertIsNotNone(productos_vendidos_context)
        
        # Solo Venta 2 (Hoy): Producto A (10 unidades), Producto C (3 unidades)
        self.assertEqual(len(productos_vendidos_context), 2, "Deberían listarse 2 productos para hoy.")
        
        self.assertEqual(productos_vendidos_context[0]['producto__nombre'], self.producto_a.nombre)
        self.assertEqual(productos_vendidos_context[0]['total_cantidad_vendida'], 10)
        self.assertEqual(productos_vendidos_context[0]['total_monto_generado'], Decimal('100.00'))
        
        self.assertEqual(productos_vendidos_context[1]['producto__nombre'], self.producto_c.nombre)
        self.assertEqual(productos_vendidos_context[1]['total_cantidad_vendida'], 3)
        self.assertEqual(productos_vendidos_context[1]['total_monto_generado'], Decimal('15.00'))

    def test_informe_productos_mas_vendidos_filtro_fecha_ayer(self):
        """Test del informe filtrando solo para ventas de ayer."""
        url_informe = reverse('informes:productos_mas_vendidos')
        fecha_ayer_str = (datetime.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')

        response = self.client.get(url_informe, {'fecha_desde': fecha_ayer_str, 'fecha_hasta': fecha_ayer_str})
        self.assertEqual(response.status_code, 200)
        productos_vendidos_context = response.context.get('productos_vendidos')
        self.assertIsNotNone(productos_vendidos_context)

        # Solo Venta 1 (Ayer): Producto A (5 unidades), Producto B (2 unidades)
        self.assertEqual(len(productos_vendidos_context), 2, "Deberían listarse 2 productos para ayer.")

        # Orden por cantidad: A (5), B (2)
        self.assertEqual(productos_vendidos_context[0]['producto__nombre'], self.producto_a.nombre)
        self.assertEqual(productos_vendidos_context[0]['total_cantidad_vendida'], 5)
        self.assertEqual(productos_vendidos_context[0]['total_monto_generado'], Decimal('50.00'))
        
        self.assertEqual(productos_vendidos_context[1]['producto__nombre'], self.producto_b.nombre)
        self.assertEqual(productos_vendidos_context[1]['total_cantidad_vendida'], 2)
        self.assertEqual(productos_vendidos_context[1]['total_monto_generado'], Decimal('40.00'))

    def test_informe_productos_mas_vendidos_filtro_rango_amplio(self):
        """Test del informe con un rango de fechas que incluye todas las ventas válidas."""
        url_informe = reverse('informes:productos_mas_vendidos')
        fecha_inicio_str = (datetime.now().date() - timedelta(days=3)).strftime('%Y-%m-%d')
        fecha_fin_str = (datetime.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')

        response = self.client.get(url_informe, {'fecha_desde': fecha_inicio_str, 'fecha_hasta': fecha_fin_str})
        self.assertEqual(response.status_code, 200)
        productos_vendidos_context = response.context.get('productos_vendidos')
        self.assertIsNotNone(productos_vendidos_context)
        # Debería ser igual al caso sin filtro
        self.assertEqual(len(productos_vendidos_context), 3) 
        self.assertEqual(productos_vendidos_context[0]['producto__nombre'], self.producto_a.nombre)
        self.assertEqual(productos_vendidos_context[0]['total_cantidad_vendida'], 15)


    def test_informe_productos_mas_vendidos_sin_ventas_en_rango(self):
        """Test del informe con un rango de fechas sin ventas."""
        url_informe = reverse('informes:productos_mas_vendidos')
        fecha_inicio_str = (datetime.now().date() - timedelta(days=10)).strftime('%Y-%m-%d')
        fecha_fin_str = (datetime.now().date() - timedelta(days=9)).strftime('%Y-%m-%d')

        response = self.client.get(url_informe, {'fecha_desde': fecha_inicio_str, 'fecha_hasta': fecha_fin_str})
        self.assertEqual(response.status_code, 200)
        productos_vendidos_context = response.context.get('productos_vendidos')
        self.assertIsNotNone(productos_vendidos_context)
        self.assertEqual(len(productos_vendidos_context), 0, "No debería haber productos si no hay ventas en el rango.")

                
    def tearDown(self):
        self.client.logout()
        super().tearDown()
