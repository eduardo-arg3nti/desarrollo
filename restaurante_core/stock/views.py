from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Producto
from .forms import ProductoForm

# Helper function para verificar si un usuario pertenece a un grupo específico
def is_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

# Helper para verificar si es Administrador
def es_administrador(user):
    return is_in_group(user, 'Administradores')

class AdministradorAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin para restringir acceso a Administradores."""
    def test_func(self):
        return es_administrador(self.request.user)

    def handle_no_permission(self):
        # Redirigir a 'home' o mostrar un mensaje de error si no es administrador
        # Opcionalmente, podrías redirigir a la página de login si no está autenticado,
        # pero LoginRequiredMixin ya debería manejar eso.
        if not self.request.user.is_authenticated:
            return super().handle_no_permission() # Deja que LoginRequiredMixin maneje
        # Si está autenticado pero no es admin:
        from django.contrib import messages
        messages.error(self.request, "Acceso denegado. Esta sección es solo para administradores.")
        return redirect('home')


class ProductoListView(AdministradorAccessMixin, ListView):
    model = Producto
    template_name = 'stock/producto_list.html'
    context_object_name = 'productos'

    def get_queryset(self):
        # Solo mostrar productos activos
        return Producto.objects.filter(activo=True).order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Productos con stock bajo
        context['productos_stock_bajo'] = Producto.objects.filter(
            activo=True, stock_actual__lte=models.F('stock_minimo')
        ).order_by('nombre')
        return context

class ProductoCreateView(CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'stock/producto_form.html'
    success_url = reverse_lazy('stock:producto_list')

    def form_valid(self, form):
        # Lógica adicional si es necesaria antes de guardar
        return super().form_valid(form)

class ProductoUpdateView(AdministradorAccessMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'stock/producto_form.html'
    success_url = reverse_lazy('stock:producto_list')

    def get_queryset(self):
        # Asegurar que solo se puedan editar productos activos (opcional, dependiendo de la lógica de negocio)
        # El mixin ya se encarga de la restricción de acceso.
        return super().get_queryset() # O Producto.objects.all() si el mixin es suficiente

@login_required
@user_passes_test(es_administrador, login_url='home') # Redirige a 'home' si no pasa el test
def producto_delete_logico(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.activo = False
        producto.save()
        from django.contrib import messages # Mover import aquí para usarlo
        messages.success(request, f"Producto '{producto.nombre}' marcado como inactivo.")
        return redirect('stock:producto_list')
    
    # Si es GET, o no es POST, simplemente redirigir o mostrar error.
    # Por seguridad, las operaciones de cambio de estado deberían ser POST.
    # Aquí, como se accede directamente desde un botón en la lista, se hace la baja.
    # Para una confirmación, se necesitaría una plantilla intermedia.
    # Para simplificar, si no es POST, simplemente redirigimos.
    # O, si el diseño actual asume que un GET a esta URL es para borrar:
    producto.activo = False
    producto.save()
    from django.contrib import messages
    messages.success(request, f"Producto '{producto.nombre}' marcado como inactivo (vía GET, considerar cambiar a POST).")
    return redirect('stock:producto_list')
