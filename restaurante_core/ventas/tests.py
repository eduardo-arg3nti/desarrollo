from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from stock.models import Producto
from ventas.models import Venta, DetalleVenta
from decimal import Decimal

class VentasIntegrationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Crear grupos
        cls.admin_group, _ = Group.objects.get_or_create(name='Administradores')
        cls.cajero_group, _ = Group.objects.get_or_create(name='Cajeros')

        # Crear usuarios
        cls.admin_user = User.objects.create_user(username='testadminventas', password='testpassword123', is_staff=True)
        cls.admin_user.groups.add(cls.admin_group)

        cls.cajero_user = User.objects.create_user(username='testcajero', password='testpassword123')
        cls.cajero_user.groups.add(cls.cajero_group)

        # Crear productos de prueba
        cls.producto1 = Producto.objects.create(
            nombre='Producto Ventas Test 1', 
            precio_costo=Decimal('5.00'), 
            precio_venta=Decimal('10.00'), 
            stock_actual=100,
            stock_minimo=10
        )
        cls.producto2 = Producto.objects.create(
            nombre='Producto Ventas Test 2', 
            precio_costo=Decimal('7.00'), 
            precio_venta=Decimal('15.00'), 
            stock_actual=50,
            stock_minimo=5
        )
        cls.producto_agotado = Producto.objects.create(
            nombre='Producto Agotado Ventas Test', 
            precio_costo=Decimal('3.00'), 
            precio_venta=Decimal('6.00'), 
            stock_actual=0 # Agotado
        )

        cls.client = Client()

    def setUp(self):
        # Loguear como cajero para la mayoría de las pruebas de ventas
        self.client.login(username='testcajero', password='testpassword123')

    def test_registro_venta_mostrador(self):
        """
        Test para registrar una venta por mostrador, incluyendo adición al carrito
        y actualización de stock.
        """
        # URL de la vista de venta por mostrador
        url_venta_mostrador = reverse('ventas:venta_mostrador')

        # 1. Añadir productos al carrito de sesión
        # Añadir 2 unidades del producto1
        # La vista VentaMostradorView usa 'producto_id_manual' en la URL y 'cantidad_add_X' en POST para JS.
        # Para probar directamente el backend, necesitamos simular lo que el JS haría:
        # enviar 'producto_id' y 'cantidad' en el cuerpo del POST.
        
        # Simular que el JS añade 'producto_id' y 'cantidad' al POST
        # Añadir 2 unidades del producto1
        response_add_p1 = self.client.post(url_venta_mostrador, {
            'producto_id': self.producto1.pk,
            'cantidad': '2',
            'action': 'add_to_cart'
        })
        self.assertEqual(response_add_p1.status_code, 302, f"No se redirigió después de añadir P1. Errores: {response_add_p1.context.get('form') if response_add_p1.context else 'N/A'}")
        cart_session = self.client.session.get('cart', {})
        self.assertIn(str(self.producto1.pk), cart_session)
        self.assertEqual(cart_session[str(self.producto1.pk)]['cantidad'], 2)

        # Añadir 1 unidad del producto2
        response_add_p2 = self.client.post(url_venta_mostrador, {
            'producto_id': self.producto2.pk,
            'cantidad': '1',
            'action': 'add_to_cart'
        })
        self.assertEqual(response_add_p2.status_code, 302, "No se redirigió después de añadir P2")
        cart_session = self.client.session.get('cart', {})
        self.assertIn(str(self.producto2.pk), cart_session)
        self.assertEqual(cart_session[str(self.producto2.pk)]['cantidad'], 1)
        
        # 2. Registrar la venta
        register_sale_data = {'action': 'register_sale'}
        response_register = self.client.post(url_venta_mostrador, data=register_sale_data)
        
        self.assertEqual(response_register.status_code, 302, "No se redirigió después de registrar la venta.")
        
        # 3. Verificar que se crea un objeto Venta
        self.assertEqual(Venta.objects.count(), 1, "No se creó un único objeto Venta.")
        venta_creada = Venta.objects.first()
        self.assertEqual(venta_creada.tipo_venta, 'mostrador')
        self.assertEqual(venta_creada.estado_pedido, 'completado')

        # 4. Verificar que se crean los DetalleVenta correctos
        detalles = DetalleVenta.objects.filter(venta=venta_creada).order_by('producto__nombre')
        self.assertEqual(detalles.count(), 2, "No se crearon dos objetos DetalleVenta.")
        
        detalle_p1 = detalles.get(producto=self.producto1)
        self.assertEqual(detalle_p1.cantidad, 2)
        self.assertEqual(detalle_p1.precio_unitario_venta, self.producto1.precio_venta)
        self.assertEqual(detalle_p1.subtotal, self.producto1.precio_venta * 2)

        detalle_p2 = detalles.get(producto=self.producto2)
        self.assertEqual(detalle_p2.cantidad, 1)
        self.assertEqual(detalle_p2.precio_unitario_venta, self.producto2.precio_venta)
        self.assertEqual(detalle_p2.subtotal, self.producto2.precio_venta * 1)
        
        expected_total_venta = (self.producto1.precio_venta * 2) + (self.producto2.precio_venta * 1)
        self.assertEqual(venta_creada.total_venta, expected_total_venta, "El total_venta no es correcto.")

        # 5. Verificar que el stock de los Productos se descuenta correctamente
        self.producto1.refresh_from_db()
        self.producto2.refresh_from_db()
        self.assertEqual(self.producto1.stock_actual, 100 - 2, "El stock del Producto 1 no se descontó correctamente.")
        self.assertEqual(self.producto2.stock_actual, 50 - 1, "El stock del Producto 2 no se descontó correctamente.")

        # 6. Verificar que el carrito de sesión se limpia después de la venta
        cart_session_after_sale = self.client.session.get('cart', {})
        self.assertEqual(len(cart_session_after_sale), 0, "El carrito de sesión no se limpió después de la venta.")

    def tearDown(self):
        self.client.logout()
        # Limpiar carritos de sesión si es necesario, aunque Django Test Client lo hace por request.
        # if 'cart' in self.client.session:
        #     del self.client.session['cart']
        #     self.client.session.save()
        super().tearDown()
