from django import forms
from .models import Operador, Vehiculo, Asignacion

# Formulario para el modelo Operador
class OperadorForm(forms.ModelForm):
    class Meta:
        model = Operador
        exclude = ['activo']


# Formulario para el modelo Vehiculo
class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        exclude = ['codigo_qr', 'activo']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['placa'].disabled = True


# Formulario para el modelo Asignacion
class AsignacionForm(forms.ModelForm):
    class Meta:
        model = Asignacion
        exclude = ['fecha_asignacion', 'total_vueltas', 'total_material', 'estado', 'ultima_vuelta_registrada_en']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['operador'].disabled = True
            self.fields['vehiculo'].disabled = True