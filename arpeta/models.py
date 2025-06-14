from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from io import BytesIO
import os
from cryptography.fernet import Fernet
import qrcode
from phonenumber_field.modelfields import PhoneNumberField


# Modelo que representa a un Operador
class Operador(models.Model):
    cedula = models.CharField(primary_key=True, max_length=8, verbose_name='Cédula')
    nombre = models.CharField(max_length=50, verbose_name='Nombre')
    apellido = models.CharField(max_length=50, verbose_name='Apellido')
    telefono = PhoneNumberField(region='VE', verbose_name='Teléfono')
    correo = models.EmailField(max_length=100, verbose_name='Correo Electrónico')
    direccion = models.TextField(verbose_name='Dirección')
    independiente = models.BooleanField(default=True, verbose_name='Independiente')
    foto_operador = models.ImageField(upload_to='operadores/', blank=True, null=True, verbose_name='Foto del Operador')
    activo = models.BooleanField(default=True, verbose_name='Activo')

    # Propiedad que devuelve "Si" o "No" para el campo independiente
    @property
    def independiente_texto(self):
        return "Si" if self.independiente else "No"

    # Propiedad que devuelve "Activo" o "Inactivo" para el campo activo
    @property
    def activo_texto(self):
        return "Activo" if self.activo else "Inactivo"

    # Método para eliminar un operador y su foto asociada
    def delete(self, *args, **kwargs):
        if self.foto_operador and os.path.isfile(self.foto_operador.path):
            os.remove(self.foto_operador.path)
        super().delete(*args, **kwargs)

    # Representación en cadena del modelo Operador
    def __str__(self):
        return f"Cédula: {self.cedula} - Operador: {self.nombre} {self.apellido}"

    # Meta clase para definir opciones adicionales del modelo
    class Meta:
        verbose_name = 'Operador'
        verbose_name_plural = 'Operadores'


# Modelo que representa una Marca de Vehículo
class Marca(models.Model):
    nombre = models.CharField(max_length=50, unique=True, verbose_name='Marca')

    # Representación en cadena del modelo Marca
    def __str__(self):
        return self.nombre

    # Meta clase para definir opciones adicionales del modelo
    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'


# Modelo que representa un Modelo de Vehículo asociado a una Marca
class Modelo(models.Model):
    nombre = models.CharField(max_length=50, verbose_name='Modelo')
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, verbose_name='Marca')

    # Representación en cadena del modelo Modelo
    def __str__(self):
        return f"{self.marca.nombre} - {self.nombre}"

    # Meta clase para definir opciones adicionales del modelo
    class Meta:
        unique_together = ('nombre', 'marca')
        verbose_name = 'Modelo'
        verbose_name_plural = 'Modelos'


# Modelo que representa un Vehículo
class Vehiculo(models.Model):
    placa = models.CharField(primary_key=True, max_length=6, verbose_name="Placa")
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE, verbose_name="Modelo")
    alto = models.DecimalField(
        decimal_places=2,
        max_digits=4,
        validators=[MinValueValidator(1.00), MaxValueValidator(4.10)],
        verbose_name="Alto (metros)")
    ancho = models.DecimalField(
        decimal_places=2,
        max_digits=4,
        validators=[MinValueValidator(1.00), MaxValueValidator(2.60)],
        verbose_name="Ancho (metros)")
    largo = models.DecimalField(
        decimal_places=2,
        max_digits=5,
        validators=[MinValueValidator(1.00), MaxValueValidator(12.20)],
        verbose_name="Largo (metros)")
    foto_vehiculo = models.ImageField(upload_to="vehiculos/", blank=True, null=True, verbose_name="Foto del Vehículo")
    codigo_qr = models.ImageField(upload_to="codigos_qr/", verbose_name="Código QR")
    activo = models.BooleanField(default=True, verbose_name="Activo")

    # Propiedad para calcular la capacidad de carga del vehículo
    @property
    def capacidad_carga(self):
        if self.alto is not None and self.ancho is not None and self.largo is not None:
            return float(self.alto) * float(self.ancho) * float(self.largo)
        return 0.00

    # Método para guardar el vehículo, generando un código QR encriptado si no existe
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs) # REVISAR: Creo que tengo que eliminar esta línea
        if not self.codigo_qr and self.placa:
            try:
                key = settings.FERNET_KEY
            except AttributeError:
                raise ImproperlyConfigured(
                    "La clave FERNET_KEY no está configurada en settings.py. "
                    "No se puede generar el código QR encriptado."
                )
            f = Fernet(key)
            placa_original_bytes = self.placa.encode('utf-8')
            placa_encriptada_bytes = f.encrypt(placa_original_bytes)
            contenido_qr_encriptado_str = placa_encriptada_bytes.decode('utf-8')
            imagen_qr_obj = qrcode.make(contenido_qr_encriptado_str)
            buffer = BytesIO()
            imagen_qr_obj.save(buffer, format="PNG")
            nombre_archivo = f"qr_vehiculo_{self.placa}.png"
            self.codigo_qr.save(nombre_archivo, ContentFile(buffer.getvalue()), save=False)
            super().save(*args, **kwargs)

    # Método para eliminar un vehículo y sus archivos asociados (foto y código QR)
    def delete(self, *args, **kwargs):
        if self.foto_vehiculo and os.path.isfile(self.foto_vehiculo.path):
            os.remove(self.foto_vehiculo.path)
        if self.codigo_qr and os.path.isfile(self.codigo_qr.path):
            os.remove(self.codigo_qr.path)
        super().delete(*args, **kwargs)

    # Representación en cadena del modelo Vehiculo
    def __str__(self):
        return f"Placa: {self.placa} - Vehíuculo: {self.modelo.marca} - {self.modelo.nombre}"

    # Meta clase para definir opciones adicionales del modelo
    class Meta:
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'


# Modelo que representa un Tipo de Material
class TipoMaterial(models.Model):
    nombre = models.CharField(max_length=50, unique=True, verbose_name='Tipo de Material')

    # Representación en cadena del modelo TipoMaterial
    def __str__(self):
        return self.nombre

    # Meta clase para definir opciones adicionales del modelo
    class Meta:
        verbose_name = 'Tipo de Material'
        verbose_name_plural = 'Tipos de Material'


# Modelo que representa una Asignación de un vehículo a un operador
class Asignacion(models.Model):
    operador = models.ForeignKey(Operador, on_delete=models.CASCADE, verbose_name='Operador')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, verbose_name='Vehículo')
    fecha_asignacion = models.DateField(verbose_name='Fecha de Asignación')
    tipo_material = models.ForeignKey(TipoMaterial, on_delete=models.CASCADE, verbose_name="Tipo de Material", null=True, blank=True)
    total_vueltas = models.IntegerField(default=0, verbose_name="Total de Vueltas")
    estado = models.BooleanField(default=True, verbose_name='Estado')
    ultima_vuelta_registrada_en = models.DateTimeField(null=True, blank=True, verbose_name='Última Vuelta Registrada en')

    # Meta clase para definir opciones adicionales del modelo
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['operador', 'vehiculo', 'fecha_asignacion'], name='unique_operador_vehiculo_fecha')
        ]
        verbose_name = 'Asignacion'
        verbose_name_plural = 'Asignaciones'

    # Propiedad para calcular el total de material transportado
    @property
    def total_material(self):
        if self.vehiculo and self.total_vueltas is not None:
            return self.total_vueltas * self.vehiculo.capacidad_carga
        return 0.00

    # Método para guardar la asignación
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    # Propiedad para obtener la fecha de asignación formateada
    @property
    def fecha_formateada(self):
        return self.fecha_asignacion.strftime("%d-%m-%Y")

    # Propiedad para obtener el texto del estado ("Activo" o "Inactivo")
    @property
    def estado_texto(self):
        return "Activo" if self.estado else "Inactivo"

    # Representación en cadena del modelo Asignacion
    def __str__(self):
        return f"Cédula Operador: {self.operador.cedula} -Placa Vehículo: {self.vehiculo.placa} - Fecha Asignación: {self.fecha_formateada} - Tipo Material: {self.tipo_material.nombre if self.tipo_material else 'N/A'} - Total Vueltas: {self.total_vueltas} - Total Material: {self.total_material} m³ - Estado: {self.estado_texto}"