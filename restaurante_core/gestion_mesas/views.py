from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.db import transaction

from .models import Mesa
from stock.models import Producto # Para GestionPedidoMesaView
from ventas.models import Venta, DetalleVenta # Para GestionPedidoMesaView
import copy # Para GestionPedidoMesaView

# Helper functions (pueden estar en un archivo utils.py común)
def is_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

def es_administrador(user):
    return is_in_group(user, 'Administradores')

def es_cajero(user):
    return is_in_group(user, 'Cajeros')

def es_camarero(user):
    return is_in_group(user, 'Camareros')

class PersonalAutorizadoMesasMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin para restringir acceso a Administradores, Cajeros o Camareros."""
    def test_func(self):
        user = self.request.user
        return es_administrador(user) or es_cajero(user) or es_camarero(user)

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "Acceso denegado. No tiene permiso para acceder a esta sección.")
        return redirect('home')


class TableroMesasView(PersonalAutorizadoMesasMixin, ListView):
    model = Mesa
    template_name = 'gestion_mesas/tablero_mesas.html'
    context_object_name = 'mesas'

    def get_queryset(self):
        # Ordenar por ubicación y luego por número de mesa para una visualización consistente
        return Mesa.objects.all().order_by('ubicacion', 'numero_mesa')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Tablero de Mesas"
        
        estado_colores_map = {
            'disponible': 'bg-success text-white',
            'ocupada': 'bg-danger text-white',
            'reservada': 'bg-warning text-dark',
            # 'necesita_limpieza': 'bg-info text-dark'
        }
        context['estado_colores'] = estado_colores_map # Aún puede ser útil para leyendas, etc.

        # Añadir la clase de color directamente a cada objeto mesa y agrupar por ubicación
        mesas_list = list(context['mesas']) # Convertir queryset a lista para poder añadir atributos
        
        mesas_por_ubicacion = {}
        for mesa in mesas_list:
            mesa.color_class = estado_colores_map.get(mesa.estado, 'bg-light') # Default color
            
            ubicacion = mesa.ubicacion or "Sin Ubicación Definida"
            if ubicacion not in mesas_por_ubicacion:
                mesas_por_ubicacion[ubicacion] = []
            mesas_por_ubicacion[ubicacion].append(mesa)
            
        context['mesas_por_ubicacion'] = mesas_por_ubicacion
        context['mesas'] = mesas_list # Sobreescribir con la lista modificada si se usa directamente
        
        return context

class GestionPedidoMesaView(PersonalAutorizadoMesasMixin, View):
    template_name = 'gestion_mesas/gestionar_pedido_mesa.html'

    def get_cart_key(self, mesa_id):
        return f'cart_mesa_{mesa_id}'

    def get_cart(self, request, mesa_id):
        return copy.deepcopy(request.session.get(self.get_cart_key(mesa_id), {}))

    def set_cart(self, request, mesa_id, cart):
        request.session[self.get_cart_key(mesa_id)] = cart
        request.session.modified = True

    def get(self, request, mesa_id):
        mesa = get_object_or_404(Mesa, pk=mesa_id)
        productos_disponibles = Producto.objects.filter(activo=True, stock_actual__gt=0).order_by('nombre')
        query = request.GET.get('q_producto')
        if query:
            productos_disponibles = productos_disponibles.filter(nombre__icontains=query)

        cart_session = self.get_cart(request, mesa_id)
        pedido_actual_items_display = [] # Para items ya en una Venta guardada
        cart_items_display = [] # Para items en el carrito de sesión (no guardados aún o añadiéndose)
        current_total = 0 # Total de la Venta guardada
        cart_total = 0 # Total del carrito de sesión

        # Información de la venta activa, si existe
        venta_actual = mesa.venta_actual 

        if venta_actual:
            # Cargar items del pedido ya guardado en la Venta
            for detalle in venta_actual.detalles.all().select_related('producto'):
                pedido_actual_items_display.append({
                    'detalle_id': detalle.pk, # Para identificarlo si se quiere modificar/eliminar
                    'producto_id': detalle.producto.pk,
                    'nombre': detalle.producto.nombre,
                    'cantidad': detalle.cantidad,
                    'precio_unitario': detalle.precio_unitario_venta,
                    'subtotal': detalle.subtotal,
                })
            current_total = venta_actual.total_venta

        # Cargar items del carrito de sesión (productos nuevos o no guardados)
        for producto_id_str, item_data in cart_session.items():
            producto_id = int(producto_id_str)
            producto = get_object_or_404(Producto, pk=producto_id) # Asumir que el producto existe
            cantidad = item_data.get('cantidad', 0)
            precio_venta = item_data.get('precio_venta', float(producto.precio_venta)) # Usar precio guardado o actual
            subtotal = precio_venta * cantidad
            cart_items_display.append({
                'producto_id': producto_id,
                'nombre': producto.nombre,
                'cantidad': cantidad,
                'precio_unitario': precio_venta,
                'subtotal': subtotal,
                'es_nuevo': True # Para diferenciar en la plantilla
            })
            cart_total += subtotal
        
        combined_total = current_total + cart_total

        context = {
            'mesa': mesa,
            'venta_actual': venta_actual,
            'productos_disponibles': productos_disponibles,
            'pedido_actual_items': pedido_actual_items_display, # Items de la Venta guardada
            'cart_items': cart_items_display, # Items del carrito de sesión
            'current_total': current_total, # Total de la Venta guardada
            'cart_total': cart_total, # Total del carrito de sesión
            'combined_total': combined_total, # Suma de ambos
            'search_query_producto': query or "",
        }
        return render(request, self.template_name, context)

    def post(self, request, mesa_id):
        mesa = get_object_or_404(Mesa, pk=mesa_id)
        action = request.POST.get('action')
        cart = self.get_cart(request, mesa_id) # Carrito de sesión para esta mesa

        # Acción: Añadir producto al pedido/carrito de la mesa
        if action == 'add_to_pedido_mesa':
            producto_id_str = request.POST.get('producto_id')
            cantidad_str = request.POST.get('cantidad', '1')
            
            if not producto_id_str or not cantidad_str:
                messages.error(request, "Falta ID de producto o cantidad.")
                return redirect('gestion_mesas:gestionar_pedido_mesa', mesa_id=mesa.pk)
            
            try:
                producto_id = int(producto_id_str)
                cantidad = int(cantidad_str)
                producto = Producto.objects.get(pk=producto_id, activo=True)
            except (ValueError, Producto.DoesNotExist):
                messages.error(request, "Producto no válido o no encontrado.")
                return redirect('gestion_mesas:gestionar_pedido_mesa', mesa_id=mesa.pk)

            if cantidad <= 0:
                messages.warning(request, "La cantidad debe ser positiva.")
            # Validar stock considerando lo que ya está en la Venta y en el carrito de sesión
            # Esta validación se hará más robusta al guardar/finalizar
            elif cantidad > producto.stock_actual :
                 messages.warning(request, f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock_actual}")
            else:
                # Si el producto ya está en el carrito de sesión, se actualiza su cantidad
                if str(producto_id) in cart:
                    cart[str(producto_id)]['cantidad'] += cantidad
                else:
                    cart[str(producto_id)] = {'cantidad': cantidad, 'precio_venta': float(producto.precio_venta)}
                messages.success(request, f"{cantidad} x {producto.nombre} añadido al pedido de la mesa.")
            self.set_cart(request, mesa_id, cart)

        # Acción: Actualizar cantidad de un item en el carrito de sesión
        elif action == 'update_cart_mesa_item': # Para items en el carrito de sesión
            producto_id_str = request.POST.get('producto_id')
            cantidad_str = request.POST.get('cantidad')
            if not producto_id_str or cantidad_str is None:
                messages.error(request, "Falta ID de producto o cantidad para actualizar.")
            else:
                try:
                    producto_id = int(producto_id_str)
                    cantidad = int(cantidad_str)
                    producto = Producto.objects.get(pk=producto_id, activo=True) # Para validar stock

                    if cantidad > 0:
                        if cantidad > producto.stock_actual:
                            messages.warning(request, f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock_actual}")
                            # No actualiza o ajusta a stock_actual (decisión de diseño)
                        else:
                            cart[str(producto_id)]['cantidad'] = cantidad
                            messages.success(request, f"Cantidad de {producto.nombre} actualizada en el carrito de la mesa.")
                    elif cantidad == 0: # Eliminar del carrito de sesión
                        if str(producto_id) in cart:
                            del cart[str(producto_id)]
                            messages.info(request, f"{producto.nombre} eliminado del carrito de la mesa.")
                except (ValueError, Producto.DoesNotExist):
                    messages.error(request, "Error al actualizar item: producto no válido.")
            self.set_cart(request, mesa_id, cart)

        # Acción: Eliminar item del carrito de sesión
        elif action == 'remove_from_cart_mesa_item': # Para items en el carrito de sesión
            producto_id_str = request.POST.get('producto_id')
            if producto_id_str in cart:
                del cart[producto_id_str]
                messages.info(request, "Producto eliminado del carrito de la mesa.")
            self.set_cart(request, mesa_id, cart)

        # Acción: Guardar el pedido (crear/actualizar Venta y Detalles, marcar mesa como ocupada)
        elif action == 'guardar_pedido_mesa':
            if not cart and not mesa.venta_actual: # Nada en sesión y no hay venta existente
                messages.warning(request, "No hay productos en el pedido para guardar.")
                return redirect('gestion_mesas:gestionar_pedido_mesa', mesa_id=mesa.pk)

            try:
                with transaction.atomic():
                    venta_obj = mesa.venta_actual
                    if not venta_obj: # Crear nueva venta si no existe una activa para la mesa
                        if not cart: # No hay items en sesión para crear una nueva venta
                            messages.warning(request, "El carrito está vacío, no se puede crear una nueva venta.")
                            return redirect('gestion_mesas:gestionar_pedido_mesa', mesa_id=mesa.pk)

                        # Validar stock antes de crear
                        for pid_str, item_data in cart.items():
                            prod = Producto.objects.select_for_update().get(pk=int(pid_str))
                            if item_data['cantidad'] > prod.stock_actual:
                                raise ValueError(f"Stock insuficiente para {prod.nombre} al crear la venta.")
                        
                        venta_obj = Venta.objects.create(
                            mesa=mesa, 
                            tipo_venta='mesa',
                            estado_pedido='en_proceso', # O 'pendiente_confirmacion', 'abierto'
                            # total_venta se actualizará con los detalles
                        )
                        mesa.venta_actual = venta_obj
                        mesa.estado = 'ocupada'
                        mesa.save(update_fields=['venta_actual', 'estado'])
                    
                    # Añadir/actualizar detalles de la venta desde el carrito de sesión
                    for producto_id_str, item_data in cart.items():
                        producto_id = int(producto_id_str)
                        producto = Producto.objects.get(pk=producto_id) # Ya validado antes o se asume que existe

                        # Validar stock al guardar (importante si el stock cambió mientras el item estaba en carrito)
                        # Esta validación es crucial aquí, incluso si se hizo al añadir al carrito
                        if item_data['cantidad'] > producto.stock_actual:
                             raise ValueError(f"Stock insuficiente para {producto.nombre} al guardar. Disponible: {producto.stock_actual}")

                        detalle, created = DetalleVenta.objects.get_or_create(
                            venta=venta_obj,
                            producto=producto,
                            defaults={'cantidad': 0, 'precio_unitario_venta': item_data['precio_venta']}
                        )
                        if created:
                            detalle.cantidad = item_data['cantidad']
                        else: # Si ya existía (ej. añadido antes y guardado), sumar cantidades
                            detalle.cantidad += item_data['cantidad']
                        
                        detalle.precio_unitario_venta = item_data['precio_venta'] # Actualizar precio por si cambió
                        detalle.save() # Esto recalculará subtotal y Venta.total_venta

                        # Descontar stock
                        producto.stock_actual -= item_data['cantidad'] # Aquí descontamos lo que se añade desde el carrito
                        producto.save(update_fields=['stock_actual'])
                    
                    # venta_obj.actualizar_total() # Se llama desde DetalleVenta.save()
                    self.set_cart(request, mesa_id, {}) # Limpiar carrito de sesión para esta mesa
                    messages.success(request, f"Pedido para la Mesa {mesa.numero_mesa} guardado exitosamente.")

            except ValueError as e:
                messages.error(request, str(e))
            except Producto.DoesNotExist:
                messages.error(request, "Error: Uno de los productos del pedido ya no existe.")
            except Exception as e:
                messages.error(request, f"Ocurrió un error inesperado al guardar el pedido: {e}")
        
        # Acción: Modificar item que YA ESTÁ en una Venta guardada
        elif action == 'update_pedido_existente_item':
            detalle_id_str = request.POST.get('detalle_id')
            nueva_cantidad_str = request.POST.get('cantidad')

            if not detalle_id_str or nueva_cantidad_str is None:
                messages.error(request, "Falta ID de detalle o cantidad.")
            else:
                try:
                    with transaction.atomic():
                        detalle_id = int(detalle_id_str)
                        nueva_cantidad = int(nueva_cantidad_str)
                        detalle = DetalleVenta.objects.select_related('producto', 'venta').get(pk=detalle_id)
                        
                        if detalle.venta != mesa.venta_actual:
                            messages.error(request, "Intento de modificar un pedido no asociado a esta mesa.")
                            return redirect('gestion_mesas:gestionar_pedido_mesa', mesa_id=mesa.pk)

                        producto = detalle.producto
                        diferencia_cantidad = nueva_cantidad - detalle.cantidad

                        if nueva_cantidad > 0:
                            if diferencia_cantidad > 0 and diferencia_cantidad > producto.stock_actual: # Pidiendo más de lo que hay
                                messages.warning(request, f"Stock insuficiente para añadir más {producto.nombre}. Disponible: {producto.stock_actual}")
                            else:
                                detalle.cantidad = nueva_cantidad
                                detalle.save() # Actualiza subtotal y total de Venta
                                producto.stock_actual -= diferencia_cantidad # Ajustar stock
                                producto.save(update_fields=['stock_actual'])
                                messages.success(request, f"Pedido de {producto.nombre} actualizado.")
                        elif nueva_cantidad == 0: # Eliminar el detalle
                            producto.stock_actual += detalle.cantidad # Devolver stock
                            producto.save(update_fields=['stock_actual'])
                            detalle.delete() # Esto también actualiza el total de la Venta
                            messages.info(request, f"{producto.nombre} eliminado del pedido.")
                except (ValueError, DetalleVenta.DoesNotExist, Producto.DoesNotExist) as e:
                    messages.error(request, f"Error al actualizar item del pedido: {e}")

        # Acción: Finalizar y Pagar Pedido
        elif action == 'finalizar_y_pagar_pedido_mesa':
            if not mesa.venta_actual:
                messages.error(request, "No hay un pedido activo en esta mesa para finalizar.")
            elif cart: # Hay items en el carrito de sesión sin guardar
                messages.warning(request, "Tiene items en el carrito de esta mesa sin guardar. Por favor, guárdelos primero o límpielos antes de finalizar.")
            else:
                try:
                    with transaction.atomic():
                        venta_a_finalizar = mesa.venta_actual
                        if venta_a_finalizar.detalles.count() == 0:
                            messages.warning(request, "No se puede finalizar un pedido vacío.")
                            # Opcional: cancelar la venta y liberar la mesa si el pedido está vacío
                            # venta_a_finalizar.estado_pedido = 'cancelado'
                            # venta_a_finalizar.save()
                            # mesa.estado = 'disponible'
                            # mesa.venta_actual = None
                            # mesa.save()
                            return redirect('gestion_mesas:gestionar_pedido_mesa', mesa_id=mesa.pk)

                        venta_a_finalizar.estado_pedido = 'completado'
                        venta_a_finalizar.save(update_fields=['estado_pedido'])

                        mesa.estado = 'disponible' # O 'necesita_limpieza'
                        mesa.venta_actual = None
                        mesa.save(update_fields=['estado', 'venta_actual'])
                        
                        # El stock ya fue descontado al guardar cada detalle.
                        # Si no fuera así, se descontaría aquí.
                        messages.success(request, f"Venta #{venta_a_finalizar.pk} para Mesa {mesa.numero_mesa} finalizada y pagada.")
                        # Redirigir a una página de confirmación de pago o al tablero
                        return redirect('gestion_mesas:tablero_mesas') # O a una vista de confirmación
                except Exception as e:
                    messages.error(request, f"Error al finalizar el pedido: {e}")

        return redirect('gestion_mesas:gestionar_pedido_mesa', mesa_id=mesa.pk)

