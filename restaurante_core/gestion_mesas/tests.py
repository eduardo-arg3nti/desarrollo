from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from stock.models import Producto
from ventas.models import Venta, DetalleVenta
from gestion_mesas.models import Mesa
from decimal import Decimal

class GestionMesasIntegrationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Crear grupos
        cls.admin_group, _ = Group.objects.get_or_create(name='Administradores')
        cls.cajero_group, _ = Group.objects.get_or_create(name='Cajeros')
        cls.camarero_group, _ = Group.objects.get_or_create(name='Camareros')

        # Crear usuarios
        cls.admin_user = User.objects.create_user(username='testadmingmesas', password='testpassword123', is_staff=True)
        cls.admin_user.groups.add(cls.admin_group)

        cls.camarero_user = User.objects.create_user(username='testcamarero', password='testpassword123')
        cls.camarero_user.groups.add(cls.camarero_group)

        # Crear productos de prueba
        cls.producto_mesa_1 = Producto.objects.create(
            nombre='Producto Mesa Test 1', 
            precio_costo=Decimal('8.00'), 
            precio_venta=Decimal('18.00'), 
            stock_actual=70,
            stock_minimo=10
        )
        cls.producto_mesa_2 = Producto.objects.create(
            nombre='Producto Mesa Test 2', 
            precio_costo=Decimal('4.00'), 
            precio_venta=Decimal('9.00'), 
            stock_actual=30,
            stock_minimo=5
        )

        # Crear una mesa de prueba
        cls.mesa1 = Mesa.objects.create(numero_mesa='M01', capacidad=4, estado='disponible')

        cls.client = Client()

    def setUp(self):
        # Loguear como camarero para estas pruebas
        self.client.login(username='testcamarero', password='testpassword123')

    def test_abrir_mesa_y_anadir_productos(self):
        """
        Test para abrir una mesa, añadir productos al carrito de sesión de la mesa,
        guardar el pedido, y verificar los estados y stock.
        """
        url_gestion_mesa = reverse('gestion_mesas:gestionar_pedido_mesa', kwargs={'mesa_id': self.mesa1.pk})

        # 1. Añadir productos al carrito de sesión de la mesa
        # Simular que el JS añade 'producto_id' y 'cantidad' al POST
        response_add_p1 = self.client.post(url_gestion_mesa, {
            'producto_id': self.producto_mesa_1.pk,
            'cantidad': '3',
            'action': 'add_to_pedido_mesa'
        })
        self.assertEqual(response_add_p1.status_code, 302, f"add_to_pedido_mesa P1: {response_add_p1.status_code}")
        cart_key = f'cart_mesa_{self.mesa1.pk}'
        cart_session_mesa = self.client.session.get(cart_key, {})
        self.assertIn(str(self.producto_mesa_1.pk), cart_session_mesa)
        self.assertEqual(cart_session_mesa[str(self.producto_mesa_1.pk)]['cantidad'], 3)

        response_add_p2 = self.client.post(url_gestion_mesa, {
            'producto_id': self.producto_mesa_2.pk,
            'cantidad': '1',
            'action': 'add_to_pedido_mesa'
        })
        self.assertEqual(response_add_p2.status_code, 302, f"add_to_pedido_mesa P2: {response_add_p2.status_code}")
        cart_session_mesa = self.client.session.get(cart_key, {})
        self.assertIn(str(self.producto_mesa_2.pk), cart_session_mesa)
        self.assertEqual(cart_session_mesa[str(self.producto_mesa_2.pk)]['cantidad'], 1)

        # 2. Guardar el pedido de la mesa
        response_guardar = self.client.post(url_gestion_mesa, {'action': 'guardar_pedido_mesa'})
        self.assertEqual(response_guardar.status_code, 302, f"guardar_pedido_mesa: {response_guardar.status_code}")

        # 3. Verificar estado de la Mesa
        self.mesa1.refresh_from_db()
        self.assertEqual(self.mesa1.estado, 'ocupada', "La mesa no cambió a estado 'ocupada'.")
        self.assertIsNotNone(self.mesa1.venta_actual, "La mesa no tiene una venta_actual asignada.")
        
        # 4. Verificar que se crea una Venta
        venta_mesa = self.mesa1.venta_actual
        self.assertIsNotNone(venta_mesa)
        self.assertEqual(venta_mesa.tipo_venta, 'mesa')
        # El estado inicial es 'en_proceso' según la lógica de la vista GestionPedidoMesaView
        self.assertEqual(venta_mesa.estado_pedido, 'en_proceso') 

        # 5. Verificar DetalleVenta
        detalles = DetalleVenta.objects.filter(venta=venta_mesa).order_by('producto__nombre')
        self.assertEqual(detalles.count(), 2)
        
        detalle_pm1 = detalles.get(producto=self.producto_mesa_1)
        self.assertEqual(detalle_pm1.cantidad, 3)
        self.assertEqual(detalle_pm1.precio_unitario_venta, self.producto_mesa_1.precio_venta)

        detalle_pm2 = detalles.get(producto=self.producto_mesa_2)
        self.assertEqual(detalle_pm2.cantidad, 1)
        self.assertEqual(detalle_pm2.precio_unitario_venta, self.producto_mesa_2.precio_venta)
        
        expected_total_venta = (self.producto_mesa_1.precio_venta * 3) + (self.producto_mesa_2.precio_venta * 1)
        self.assertEqual(venta_mesa.total_venta, expected_total_venta)

        # 6. Verificar descuento de Stock
        self.producto_mesa_1.refresh_from_db()
        self.producto_mesa_2.refresh_from_db()
        self.assertEqual(self.producto_mesa_1.stock_actual, 70 - 3)
        self.assertEqual(self.producto_mesa_2.stock_actual, 30 - 1)
        
        # 7. Verificar que el carrito de sesión de la mesa se limpia
        cart_session_mesa_after_save = self.client.session.get(cart_key, {})
        self.assertEqual(len(cart_session_mesa_after_save), 0)


    def test_finalizar_pedido_mesa(self):
        """
        Test para finalizar un pedido de mesa previamente abierto.
        """
        # Configurar una mesa ocupada con una venta y detalles
        stock_inicial_p1 = self.producto_mesa_1.stock_actual
        
        venta_activa = Venta.objects.create(
            mesa=self.mesa1, 
            tipo_venta='mesa', 
            estado_pedido='en_proceso' 
            # total_venta se calculará automáticamente
        )
        DetalleVenta.objects.create(
            venta=venta_activa, 
            producto=self.producto_mesa_1, 
            cantidad=2, 
            precio_unitario_venta=self.producto_mesa_1.precio_venta
        ) # Esto actualiza el total y descuenta stock si la lógica estuviera en save() de DetalleVenta
          # En nuestro caso, el stock se descuenta en la vista al 'guardar_pedido_mesa'.
          # Para este test, asumimos que el stock ya fue descontado al crear el DetalleVenta para la venta activa.
          # Si no, tendríamos que descontarlo manualmente aquí para que la lógica de 'devolver stock' funcione.
          # En la implementación actual, el stock se descuenta al guardar el pedido.
          # Para este test, el detalle ya existe, así que el stock ya debería estar descontado.
          # No, la vista GestionPedidoMesaView descuenta el stock al 'guardar_pedido_mesa'
          # y lo devuelve/ajusta al 'update_pedido_existente_item'.
          # Para este test, el detalle ya existe, así que el stock ya debería estar descontado.
          # Si el detalle se crea aquí directamente, el stock no se toca por la vista.
          # Vamos a simular el estado post-guardado del pedido:
        self.producto_mesa_1.stock_actual = stock_inicial_p1 - 2
        self.producto_mesa_1.save()

        self.mesa1.venta_actual = venta_activa
        self.mesa1.estado = 'ocupada'
        self.mesa1.save()
        
        # Asegurar que el carrito de sesión para esta mesa está vacío antes de finalizar
        cart_key = f'cart_mesa_{self.mesa1.pk}'
        if cart_key in self.client.session:
            del self.client.session[cart_key]
            self.client.session.save()

        url_gestion_mesa = reverse('gestion_mesas:gestionar_pedido_mesa', kwargs={'mesa_id': self.mesa1.pk})

        # Simular la acción "Finalizar y Pagar Pedido"
        response_finalizar = self.client.post(url_gestion_mesa, {'action': 'finalizar_y_pagar_pedido_mesa'})
        
        self.assertEqual(response_finalizar.status_code, 302, f"Finalizar pedido: {response_finalizar.status_code}")
        self.assertRedirects(response_finalizar, reverse('gestion_mesas:tablero_mesas'))

        # Verificar estado de la Mesa
        self.mesa1.refresh_from_db()
        self.assertEqual(self.mesa1.estado, 'disponible', "La mesa no volvió a 'disponible'.")
        self.assertIsNone(self.mesa1.venta_actual, "venta_actual de la mesa no es None.")

        # Verificar estado de la Venta
        venta_activa.refresh_from_db()
        self.assertEqual(venta_activa.estado_pedido, 'completado', "La venta no cambió a 'completado'.")
        
        # El stock no debería cambiar al finalizar, ya se descontó al guardar/modificar.
        self.producto_mesa_1.refresh_from_db()
        self.assertEqual(self.producto_mesa_1.stock_actual, stock_inicial_p1 - 2)


    def tearDown(self):
        self.client.logout()
        # Limpiar carritos de sesión si es necesario
        # for key in list(self.client.session.keys()):
        #     if key.startswith('cart_mesa_'):
        #         del self.client.session[key]
        # self.client.session.save()
        super().tearDown()
