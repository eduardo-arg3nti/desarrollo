from django import forms

class DateRangeFilterForm(forms.Form):
    fecha_desde = forms.DateField(
        label='Desde',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    fecha_hasta = forms.DateField(
        label='Hasta',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get("fecha_desde")
        fecha_hasta = cleaned_data.get("fecha_hasta")

        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise forms.ValidationError("La fecha 'Desde' no puede ser posterior a la fecha 'Hasta'.")
        
        return cleaned_data
