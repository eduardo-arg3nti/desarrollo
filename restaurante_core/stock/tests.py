from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from stock.models import Producto
from decimal import Decimal

class ProductoIntegrationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Crear grupo de Administradores si no existe
        cls.admin_group, _ = Group.objects.get_or_create(name='Administradores')
        
        # Crear usuario administrador
        cls.admin_user = User.objects.create_user(username='testadminstock', password='testpassword123', is_staff=True)
        cls.admin_user.groups.add(cls.admin_group)
        
        cls.client = Client()

    def setUp(self):
        # Loguear el usuario administrador antes de cada test que lo requiera
        self.client.login(username='testadminstock', password='testpassword123')

    def test_creacion_producto(self):
        """
        Test para verificar la creación de un producto a través de ProductoCreateView.
        """
        # URL de la vista de creación
        url_creacion = reverse('stock:producto_create')
        
        # Datos del producto a crear
        producto_data = {
            'nombre': 'Nuevo Producto Test Creacion',
            'descripcion': 'Descripción de prueba para creación.',
            'precio_costo': '12.50',
            'precio_venta': '25.00',
            'stock_actual': '150',
            'stock_minimo': '20',
            'categoria': 'Pruebas Crear',
            'activo': True # Checkbox activo
        }

        # Simular un POST a la vista
        response = self.client.post(url_creacion, data=producto_data)

        # 1. Verificar redirección a la lista de productos (código 302)
        self.assertEqual(response.status_code, 302, "La creación no redirigió correctamente (esperado 302).")
        self.assertRedirects(response, reverse('stock:producto_list'), 
                             msg_prefix="No se redirigió a la lista de productos después de la creación.")

        # 2. Verificar que el producto se crea en la base de datos
        try:
            producto_creado = Producto.objects.get(nombre='Nuevo Producto Test Creacion')
        except Producto.DoesNotExist:
            self.fail("El producto 'Nuevo Producto Test Creacion' no fue creado en la base de datos.")

        self.assertEqual(producto_creado.descripcion, producto_data['descripcion'])
        self.assertEqual(producto_creado.precio_costo, Decimal(producto_data['precio_costo']))
        self.assertEqual(producto_creado.precio_venta, Decimal(producto_data['precio_venta']))
        self.assertEqual(producto_creado.stock_actual, int(producto_data['stock_actual']))
        self.assertEqual(producto_creado.stock_minimo, int(producto_data['stock_minimo']))
        self.assertEqual(producto_creado.categoria, producto_data['categoria'])
        self.assertTrue(producto_creado.activo)
        
        # (Opcional) Verificar mensaje de éxito si se implementan mensajes en ProductoCreateView
        # Esto requeriría que la vista de creación añada un mensaje con Django's messages framework.
        # response_redirected = self.client.get(response.url, follow=True)
        # self.assertContains(response_redirected, "Producto creado exitosamente", 
        #                     msg_prefix="No se mostró mensaje de éxito.")

    def test_producto_delete_logico(self):
        """ Test para la baja lógica de un producto. """
        producto_a_eliminar = Producto.objects.create(
            nombre='Producto Para Eliminar Test',
            precio_costo=Decimal('10.00'),
            precio_venta=Decimal('20.00'),
            stock_actual=50,
            activo=True
        )
        url_eliminacion = reverse('stock:producto_delete', kwargs={'pk': producto_a_eliminar.pk})
        
        # La vista actual en stock/views.py realiza la baja lógica con GET o POST.
        # Para una prueba más robusta y segura, la vista debería idealmente requerir POST.
        # Aquí probamos el comportamiento actual.
        response = self.client.post(url_eliminacion) # Usar POST para la prueba
        
        self.assertEqual(response.status_code, 302, f"La eliminación no redirigió (esperado 302, obtenido {response.status_code}). URL: {url_eliminacion}")
        self.assertRedirects(response, reverse('stock:producto_list'), 
                             msg_prefix="No se redirigió a la lista de productos después de la eliminación.")
        
        producto_actualizado = Producto.objects.get(pk=producto_a_eliminar.pk)
        self.assertFalse(producto_actualizado.activo, "El producto no fue marcado como inactivo.")

    # El test de "Actualización de Stock (indirecto)" se cubrirá en ventas/tests.py,
    # ya que el stock se actualiza como efecto secundario de una venta.
    # No hay una vista directa para "actualizar stock" que no sea el form de Producto.

    def tearDown(self):
        self.client.logout()
        super().tearDown()
