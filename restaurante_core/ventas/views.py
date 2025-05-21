from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from stock.models import Producto
from .models import Venta, DetalleVenta
import copy # Para deepcopy del carrito

# Helper functions para verificar grupos (pueden moverse a un archivo utils.py si se usan en múltiples apps)
def is_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

def es_administrador(user):
    return is_in_group(user, 'Administradores')

def es_cajero(user):
    return is_in_group(user, 'Cajeros')

class VentasAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin para restringir acceso a Administradores o Cajeros."""
    def test_func(self):
        return es_administrador(self.request.user) or es_cajero(self.request.user)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "Acceso denegado. Esta sección es para Administradores o Cajeros.")
        return redirect('home')


class VentaMostradorView(VentasAccessMixin, View):
    template_name = 'ventas/venta_mostrador.html'

    def get_cart(self, request):
        cart = request.session.get('cart', {})
        # Asegurarse de que el carrito en sesión sea una copia profunda para evitar modificarlo accidentalmente
        # al pasarlo al contexto y luego modificarlo en la vista.
        return copy.deepcopy(cart)

    def set_cart(self, request, cart):
        request.session['cart'] = cart
        request.session.modified = True


    def get(self, request, *args, **kwargs):
        productos = Producto.objects.filter(activo=True, stock_actual__gt=0).order_by('nombre')
        query = request.GET.get('q')
        if query:
            productos = productos.filter(nombre__icontains=query)

        cart_session = self.get_cart(request)
        cart_display = []
        cart_total = 0

        for producto_id, item_data in cart_session.items():
            producto = Producto.objects.get(pk=producto_id) # Asumimos que el producto existe
            cantidad = item_data.get('cantidad', 0)
            subtotal = producto.precio_venta * cantidad
            cart_display.append({
                'producto_id': producto_id,
                'nombre': producto.nombre,
                'cantidad': cantidad,
                'precio_unitario': producto.precio_venta,
                'subtotal': subtotal,
            })
            cart_total += subtotal
        
        context = {
            'productos': productos,
            'cart_items': cart_display,
            'cart_total': cart_total,
            'search_query': query or ""
        }
        return render(request, self.template_name, context)


class ImprimirComandaView(LoginRequiredMixin, View): # Solo requiere login, el contexto lo da la venta
    template_name = 'ventas/comanda_print.html'

    def get(self, request, venta_id):
        venta = get_object_or_404(Venta.objects.select_related('mesa'), pk=venta_id)
        # Aquí se podría añadir una comprobación si el usuario tiene permiso para ver esta venta específica,
        # pero por ahora, si está logueado y tiene la URL, puede imprimirla.
        detalles = venta.detalles.all().select_related('producto') 

        context = {
            'venta': venta,
            'detalles': detalles,
        }
        return render(request, self.template_name, context)


class GestionDeliveryView(VentasAccessMixin, View):
    template_name = 'ventas/gestion_delivery.html'
    cart_session_key = 'cart_delivery'

    def get_cart(self, request):
        return copy.deepcopy(request.session.get(self.cart_session_key, {}))

    def set_cart(self, request, cart):
        request.session[self.cart_session_key] = cart
        request.session.modified = True

    def get(self, request, *args, **kwargs):
        productos = Producto.objects.filter(activo=True, stock_actual__gt=0).order_by('nombre')
        query = request.GET.get('q_producto')
        if query:
            productos = productos.filter(nombre__icontains=query)

        cart_session = self.get_cart(request)
        cart_display = []
        cart_total = 0

        for producto_id_str, item_data in cart_session.items():
            producto_id = int(producto_id_str)
            # Usar get_object_or_404 es más seguro, pero para un carrito interno,
            # se asume que el producto existe si está en el carrito.
            # Considerar manejo de errores si el producto es eliminado mientras está en carrito.
            try:
                producto = Producto.objects.get(pk=producto_id)
                cantidad = item_data.get('cantidad', 0)
                precio_venta = item_data.get('precio_venta', float(producto.precio_venta))
                subtotal = precio_venta * cantidad
                cart_display.append({
                    'producto_id': producto_id,
                    'nombre': producto.nombre,
                    'cantidad': cantidad,
                    'precio_unitario': precio_venta,
                    'subtotal': subtotal,
                })
                cart_total += subtotal
            except Producto.DoesNotExist:
                # Producto no existe, podría eliminarse del carrito aquí o mostrar un error
                # Para simplificar, lo omitimos en la visualización.
                # Una mejor solución sería limpiar el carrito de items inválidos.
                pass
        
        # Datos del cliente guardados en sesión para persistencia entre requests GET/POST si no se guarda el pedido.
        # Esto es útil si el usuario añade productos, luego llena datos, y vuelve a añadir.
        cliente_data_form = {
            'cliente_nombre': request.session.get('delivery_cliente_nombre', ''),
            'cliente_direccion': request.session.get('delivery_cliente_direccion', ''),
            'cliente_telefono': request.session.get('delivery_cliente_telefono', ''),
        }

        context = {
            'productos_disponibles': productos,
            'cart_items': cart_display,
            'cart_total': cart_total,
            'search_query_producto': query or "",
            'cliente_data_form': cliente_data_form, # Para pre-llenar el formulario
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        cart = self.get_cart(request)

        # Guardar datos del cliente en sesión temporalmente cada vez que se interactúa con el formulario
        # para que no se pierdan si se añade/quita un producto.
        if request.POST.get('cliente_nombre') is not None: # Si el campo está presente en el POST
            request.session['delivery_cliente_nombre'] = request.POST.get('cliente_nombre', '')
            request.session['delivery_cliente_direccion'] = request.POST.get('cliente_direccion', '')
            request.session['delivery_cliente_telefono'] = request.POST.get('cliente_telefono', '')
            request.session.modified = True


        if action == 'add_to_delivery_cart':
            producto_id_str = request.POST.get('producto_id')
            cantidad_str = request.POST.get('cantidad', '1')
            
            if not producto_id_str or not cantidad_str:
                messages.error(request, "Falta ID de producto o cantidad.")
            else:
                try:
                    producto_id = int(producto_id_str)
                    cantidad = int(cantidad_str)
                    producto = Producto.objects.get(pk=producto_id, activo=True)

                    if cantidad <= 0:
                        messages.warning(request, "La cantidad debe ser positiva.")
                    elif producto.stock_actual == 0:
                        messages.error(request, f"'{producto.nombre}' está agotado.")
                    elif str(producto_id) in cart:
                        nueva_cantidad = cart[str(producto_id)].get('cantidad', 0) + cantidad
                        if nueva_cantidad > producto.stock_actual:
                            messages.warning(request, f"Stock insuficiente para '{producto.nombre}'. Solicitados: {nueva_cantidad}, Disponible: {producto.stock_actual}, En carrito: {cart[str(producto_id)].get('cantidad', 0)}")
                        else:
                            cart[str(producto_id)]['cantidad'] = nueva_cantidad
                            messages.success(request, f"Cantidad de '{producto.nombre}' actualizada en el carrito de delivery.")
                    elif cantidad > producto.stock_actual:
                        messages.warning(request, f"Stock insuficiente para '{producto.nombre}'. Solicitados: {cantidad}, Disponible: {producto.stock_actual}")
                    else:
                        cart[str(producto_id)] = {'cantidad': cantidad, 'precio_venta': float(producto.precio_venta)}
                        messages.success(request, f"'{producto.nombre}' añadido al carrito de delivery.")
                except (ValueError, Producto.DoesNotExist):
                    messages.error(request, "Producto no válido o no encontrado.")
            self.set_cart(request, cart)

        elif action == 'update_delivery_cart_item':
            producto_id_str = request.POST.get('producto_id')
            cantidad_str = request.POST.get('cantidad')
            if not producto_id_str or cantidad_str is None:
                messages.error(request, "Falta ID de producto o cantidad para actualizar.")
            else:
                try:
                    producto_id = int(producto_id_str)
                    cantidad = int(cantidad_str)
                    producto = Producto.objects.get(pk=producto_id, activo=True)

                    if cantidad > 0:
                        if cantidad > producto.stock_actual:
                             messages.warning(request, f"Stock insuficiente para '{producto.nombre}'. Disponible: {producto.stock_actual}")
                        else:
                            cart[str(producto_id)]['cantidad'] = cantidad
                            messages.success(request, f"Cantidad de '{producto.nombre}' actualizada.")
                    elif cantidad == 0:
                        if str(producto_id) in cart:
                            del cart[str(producto_id)]
                            messages.info(request, f"'{producto.nombre}' eliminado del carrito de delivery.")
                except (ValueError, Producto.DoesNotExist):
                    messages.error(request, "Error al actualizar item: producto no válido.")
            self.set_cart(request, cart)

        elif action == 'remove_from_delivery_cart_item':
            producto_id_str = request.POST.get('producto_id')
            if producto_id_str in cart:
                # Para mensaje amigable
                nombre_producto = "Producto"
                try: producto = Producto.objects.get(pk=int(producto_id_str)); nombre_producto = producto.nombre
                except: pass
                del cart[producto_id_str]
                messages.info(request, f"'{nombre_producto}' eliminado del carrito de delivery.")
            self.set_cart(request, cart)

        elif action == 'clear_delivery_cart':
            self.set_cart(request, {})
            messages.info(request, "Carrito de delivery limpiado.")

        elif action == 'register_delivery_order':
            if not cart:
                messages.error(request, "El carrito está vacío. No se puede registrar el pedido de delivery.")
                return redirect('ventas:gestion_delivery')

            cliente_nombre = request.POST.get('cliente_nombre', '').strip()
            cliente_direccion = request.POST.get('cliente_direccion', '').strip()
            cliente_telefono = request.POST.get('cliente_telefono', '').strip()

            if not cliente_nombre or not cliente_direccion or not cliente_telefono:
                messages.error(request, "Los datos del cliente (nombre, dirección, teléfono) son obligatorios para delivery.")
                # No redirigir, para que pueda corregir los datos manteniendo el carrito.
                # El GET se encargará de repoblar el formulario con los datos de sesión.
                return self.get(request, *args, **kwargs) # Re-renderizar la página con el error y datos

            try:
                with transaction.atomic():
                    # Validar stock ANTES de crear la Venta
                    for producto_id_str, item_data in cart.items():
                        producto = Producto.objects.select_for_update().get(pk=int(producto_id_str))
                        if item_data['cantidad'] > producto.stock_actual:
                            raise ValueError(f"Stock insuficiente para {producto.nombre} al registrar el pedido. Disponible: {producto.stock_actual}")
                    
                    total_venta_calculado = sum(
                        item_data['cantidad'] * item_data['precio_venta'] for item_data in cart.values()
                    )
                    
                    venta = Venta.objects.create(
                        tipo_venta='delivery',
                        estado_pedido='pendiente', # O 'confirmado' si se asume que se confirma al crear
                        total_venta=total_venta_calculado,
                        cliente_nombre=cliente_nombre,
                        cliente_direccion=cliente_direccion,
                        cliente_telefono=cliente_telefono
                    )

                    for producto_id_str, item_data in cart.items():
                        producto = Producto.objects.get(pk=int(producto_id_str)) # Ya validado
                        
                        DetalleVenta.objects.create(
                            venta=venta,
                            producto=producto,
                            cantidad=item_data['cantidad'],
                            precio_unitario_venta=item_data['precio_venta']
                        )
                        
                        producto.stock_actual -= item_data['cantidad']
                        producto.save(update_fields=['stock_actual'])
                    
                    # venta.actualizar_total() # Se llama desde DetalleVenta.save()
                    self.set_cart(request, {}) # Limpiar carrito de delivery
                    # Limpiar datos del cliente de la sesión
                    for key in ['delivery_cliente_nombre', 'delivery_cliente_direccion', 'delivery_cliente_telefono']:
                        if key in request.session:
                            del request.session[key]
                    request.session.modified = True
                    
                    messages.success(request, f"Pedido de Delivery #{venta.pk} registrado exitosamente.")
                    # Podría redirigirse a una vista de confirmación específica o a un listado de pedidos.
                    # Por ahora, redirigimos de nuevo a la misma página (que estará limpia).
                    return redirect('ventas:gestion_delivery') # O a una nueva 'delivery_confirmacion'

            except ValueError as e:
                messages.error(request, str(e))
            except Producto.DoesNotExist:
                messages.error(request, "Error: Uno de los productos en el carrito ya no existe.")
            except Exception as e:
                messages.error(request, f"Ocurrió un error inesperado al registrar el pedido: {e}")
            
            # Si hubo error, no redirigir, los mensajes se mostrarán en la misma página.
            # Se re-renderiza la página con el GET para mostrar el estado actual.
            return self.get(request, *args, **kwargs)


        # Si ninguna acción POST principal coincide, redirigir a la vista GET (para actualizar visualización del carrito, etc.)
        # Esto también cubre el caso donde solo se actualizaron los datos del cliente sin otra acción del carrito.
        return redirect('ventas:gestion_delivery')


class ListaPedidosDeliveryView(VentasAccessMixin, View):
    template_name = 'ventas/delivery_pedidos_pendientes.html'

    def get(self, request, *args, **kwargs):
        # Estados que se consideran "pendientes" o que requieren acción para delivery
        estados_pendientes = ['pendiente', 'confirmado', 'en_preparacion', 'listo_para_despacho', 'en_camino']
        # Se incluye 'en_camino' para que se puedan seguir viendo y actualizando a 'entregado'
        
        pedidos = Venta.objects.filter(
            tipo_venta='delivery',
            estado_pedido__in=estados_pendientes
        ).order_by('fecha_hora') # Más antiguos primero para priorizar

        context = {
            'pedidos_delivery': pedidos,
            'estados_posibles': Venta.ESTADOS_PEDIDO 
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        venta_id = request.POST.get('venta_id')
        nuevo_estado = request.POST.get('nuevo_estado')

        if action == 'cambiar_estado_pedido' and venta_id and nuevo_estado:
            try:
                venta = Venta.objects.get(pk=venta_id, tipo_venta='delivery')
                
                estado_valido = any(nuevo_estado == estado_choice[0] for estado_choice in Venta.ESTADOS_PEDIDO)
                
                if estado_valido:
                    # Lógica de transición de estados (ejemplo básico)
                    # Un estado 'entregado' o 'cancelado' no debería poder cambiarse fácilmente.
                    if venta.estado_pedido in ['entregado', 'cancelado']:
                        messages.warning(request, f"El pedido #{venta.pk} ya está '{venta.get_estado_pedido_display()}' y no se puede cambiar su estado desde aquí.")
                        return redirect('ventas:lista_pedidos_delivery')

                    venta.estado_pedido = nuevo_estado
                    venta.save(update_fields=['estado_pedido'])
                    messages.success(request, f"Estado del Pedido #{venta.pk} actualizado a '{venta.get_estado_pedido_display()}'.")
                else:
                    messages.error(request, "Estado no válido seleccionado.")
            except Venta.DoesNotExist:
                messages.error(request, "Pedido no encontrado.")
            except Exception as e:
                messages.error(request, f"Error al cambiar estado: {e}")
        
        return redirect('ventas:lista_pedidos_delivery')

class VentaMostradorConfirmacionView(LoginRequiredMixin, View): # Solo login, el contexto lo da la venta
    template_name = 'ventas/venta_confirmacion.html'

    def get(self, request, venta_id):
        venta = get_object_or_404(Venta, pk=venta_id)
        # Similar a ImprimirComandaView, se podría añadir lógica de permiso específica si fuera necesario.
        detalles = DetalleVenta.objects.filter(venta=venta)
        context = {
            'venta': venta,
            'detalles': detalles
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs): # POST method was in VentaMostradorView but not in VentaMostradorConfirmacionView
        # This POST method seems to be a leftover from VentaMostradorView.
        # VentaMostradorConfirmacionView is typically a GET-only view.
        # If there are POST actions intended for this view, they should be defined.
        # For now, assuming it's not needed and was a copy-paste artifact.
        # If it were needed, it would be something like:
        # action = request.POST.get('action')
        # if action == 'alguna_accion_de_confirmacion':
        #    ...
        # return redirect(...) or render(...)
        
        # Fallback or error if unexpected POST
        messages.error(request, "Acción no permitida en esta página.")
        return redirect('home') # Or wherever is appropriate


    def post(self, request, *args, **kwargs): # This was the original VentaMostradorView post method. Removing the duplicate definition.
        action = request.POST.get('action')
        cart = self.get_cart(request) # Obtener una copia del carrito para modificarla

        if action == 'add_to_cart':
            producto_id = request.POST.get('producto_id')
            cantidad = int(request.POST.get('cantidad', 1))
            
            if not producto_id:
                messages.error(request, "ID de producto no proporcionado.")
                return redirect('ventas:venta_mostrador')

            try:
                producto = Producto.objects.get(pk=producto_id, activo=True)
            except Producto.DoesNotExist:
                messages.error(request, "Producto no encontrado o no está activo.")
                return redirect('ventas:venta_mostrador')

            if cantidad <= 0:
                messages.warning(request, "La cantidad debe ser mayor que cero.")
            elif producto.stock_actual == 0:
                 messages.error(request, f"El producto '{producto.nombre}' está agotado.")
            elif producto_id in cart:
                # Si ya está, actualizamos la cantidad comprobando stock
                nueva_cantidad = cart[producto_id].get('cantidad',0) + cantidad
                if nueva_cantidad > producto.stock_actual:
                    messages.warning(request, f"No hay suficiente stock para '{producto.nombre}'. Disponible: {producto.stock_actual}. En carrito ya: {cart[producto_id].get('cantidad',0)}")
                    # Opcional: ajustar a stock máximo disponible
                    # cart[producto_id]['cantidad'] = producto.stock_actual
                else:
                    cart[producto_id]['cantidad'] = nueva_cantidad
                    messages.success(request, f"Cantidad de '{producto.nombre}' actualizada en el carrito.")
            elif cantidad > producto.stock_actual:
                messages.warning(request, f"No hay suficiente stock para '{producto.nombre}'. Solicitados: {cantidad}, Disponible: {producto.stock_actual}")
            else:
                cart[producto_id] = {'cantidad': cantidad, 'precio_venta': float(producto.precio_venta)}
                messages.success(request, f"'{producto.nombre}' añadido al carrito.")
            
            self.set_cart(request, cart) # Guardar el carrito modificado

        elif action == 'update_cart_item':
            producto_id = request.POST.get('producto_id')
            cantidad = int(request.POST.get('cantidad', 0))
            
            if producto_id in cart:
                try:
                    producto = Producto.objects.get(pk=producto_id, activo=True)
                    if cantidad > 0:
                        if cantidad > producto.stock_actual:
                             messages.warning(request, f"Stock insuficiente para '{producto.nombre}'. Disponible: {producto.stock_actual}")
                             # Opcional: no actualizar o ajustar a stock_actual
                        else:
                            cart[producto_id]['cantidad'] = cantidad
                            messages.success(request, f"Cantidad de '{producto.nombre}' actualizada.")
                    elif cantidad == 0: # Si la cantidad es 0, eliminar el item
                        del cart[producto_id]
                        messages.info(request, f"'{producto.nombre}' eliminado del carrito.")
                except Producto.DoesNotExist:
                    messages.error(request, "Producto no encontrado.")
                    if producto_id in cart: del cart[producto_id] # Eliminar si ya no existe
            self.set_cart(request, cart)


        elif action == 'remove_from_cart':
            producto_id = request.POST.get('producto_id')
            if producto_id in cart:
                nombre_producto = "Producto"
                try:
                    # Para mensaje amigable
                    producto = Producto.objects.get(pk=producto_id)
                    nombre_producto = producto.nombre
                except Producto.DoesNotExist:
                    pass # El producto ya no existe, pero igual lo quitamos del carrito
                del cart[producto_id]
                messages.info(request, f"'{nombre_producto}' eliminado del carrito.")
            self.set_cart(request, cart)

        elif action == 'clear_cart':
            cart = {}
            self.set_cart(request, cart)
            messages.info(request, "Carrito limpiado.")

        elif action == 'register_sale':
            if not cart:
                messages.error(request, "El carrito está vacío. No se puede registrar la venta.")
                return redirect('ventas:venta_mostrador')

            try:
                with transaction.atomic():
                    # 1. Validar stock de todos los productos en el carrito ANTES de crear la venta
                    for producto_id, item_data in cart.items():
                        producto = Producto.objects.select_for_update().get(pk=producto_id) # Bloquear fila
                        if item_data['cantidad'] > producto.stock_actual:
                            raise ValueError(f"Stock insuficiente para {producto.nombre} al momento de registrar la venta. Disponible: {producto.stock_actual}")
                    
                    # 2. Crear la Venta
                    total_venta_calculado = sum(
                        item_data['cantidad'] * item_data['precio_venta'] for item_data in cart.values()
                    )
                    
                    venta = Venta.objects.create(
                        tipo_venta='mostrador',
                        total_venta=total_venta_calculado, # Se recalculará con actualizar_total, pero es bueno tenerlo
                        estado_pedido='completado' # Para ventas por mostrador, se asume completado
                    )

                    # 3. Crear Detalles de Venta y actualizar stock
                    for producto_id, item_data in cart.items():
                        producto = Producto.objects.get(pk=producto_id) # Ya validado y bloqueado
                        
                        DetalleVenta.objects.create(
                            venta=venta,
                            producto=producto,
                            cantidad=item_data['cantidad'],
                            precio_unitario_venta=item_data['precio_venta'] # Precio al momento de añadir al carrito
                        )
                        
                        # Actualizar stock del producto
                        producto.stock_actual -= item_data['cantidad']
                        producto.save(update_fields=['stock_actual'])
                    
                    # venta.actualizar_total() # Llamado desde DetalleVenta.save()

                    # 4. Limpiar carrito
                    self.set_cart(request, {}) # carrito vacío
                    
                    messages.success(request, f"Venta #{venta.pk} registrada exitosamente.")
                    # Redirigir a una página de confirmación o de vuelta con mensaje
                    return redirect('ventas:venta_mostrador_confirmacion', venta_id=venta.pk)

            except ValueError as e: # Error de validación de stock u otro
                messages.error(request, str(e))
            except Producto.DoesNotExist:
                messages.error(request, "Error: Uno de los productos en el carrito ya no existe.")
            except Exception as e:
                messages.error(request, f"Ocurrió un error inesperado al registrar la venta: {e}")
            
            # Si hubo error, no redirigir, se mostrarán los mensajes en la misma página
            # y el carrito no se habrá limpiado.

        return redirect('ventas:venta_mostrador')


class VentaMostradorConfirmacionView(View):
    template_name = 'ventas/venta_confirmacion.html'

    def get(self, request, venta_id):
        venta = get_object_or_404(Venta, pk=venta_id)
        detalles = DetalleVenta.objects.filter(venta=venta)
        context = {
            'venta': venta,
            'detalles': detalles
        }
        return render(request, self.template_name, context)
