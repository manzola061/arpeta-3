from django.contrib import admin
from .models import Operador, Marca, Modelo, Vehiculo, TipoMaterial, Asignacion

admin.site.register(Operador)
admin.site.register(Marca)
admin.site.register(Modelo)
admin.site.register(Vehiculo)
admin.site.register(TipoMaterial)
admin.site.register(Asignacion)