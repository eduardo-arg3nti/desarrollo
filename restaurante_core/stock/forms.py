from django import forms
from .models import Producto

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio_costo', 'precio_venta', 'stock_actual', 'stock_minimo', 'categoria', 'activo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        self.fields['activo'].widget.attrs['class'] = 'form-check-input'

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        # Si se está actualizando una instancia y el nombre no ha cambiado, no validar unicidad.
        if self.instance and self.instance.pk and self.instance.nombre == nombre:
            return nombre
        if Producto.objects.filter(nombre=nombre).exists():
            raise forms.ValidationError("Ya existe un producto con este nombre.")
        return nombre
