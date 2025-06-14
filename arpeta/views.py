import os
import json
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import EmailMessage, send_mail
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Operador, Vehiculo, TipoMaterial, Asignacion, Marca, Modelo
from .forms import OperadorForm, VehiculoForm, AsignacionForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from cryptography.fernet import Fernet, InvalidToken
from django.core.exceptions import ImproperlyConfigured
from datetime import timedelta
from django.views.decorators.http import require_POST


# Función para verificar si el usuario pertenece al grupo de administración
def is_administracion(user):
    return user.groups.filter(name='Administracion').exists()


# Función para verificar si el usuario pertenece al grupo de gerente
def is_gerente(user):
    return user.groups.filter(name='Gerente').exists()


# Función para verificar si el usuario pertenece al grupo de nomina
def is_nomina(user):
    return user.groups.filter(name='Nomina').exists()


# Vista para redirigir a la página de inicio según el grupo del usuario
def inicio_redirect(request):
    if request.user.is_authenticated:
        if is_administracion(request.user):
            return redirect('inicio_administracion')
        elif is_gerente(request.user):
            return redirect('inicio_gerente')
        elif is_nomina(request.user):
            return redirect('inicio_nomina')
        else:
            return HttpResponse("No tienes permisos para acceder a esta sección. Por favor, contacta al administrador.", status=403)
    else:
        return redirect('login')


# Vista para el inicio de sesión
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                if user.groups.filter(name='Administracion').exists():
                    return redirect('inicio_administracion')
                elif user.groups.filter(name='Gerente').exists():
                    return redirect('inicio_gerente')
                elif user.groups.filter(name='Nomina').exists():
                    return redirect('inicio_nomina')
                else:
                    return redirect('inicio_redirect')
            else:
                messages.error(request, "Correo o contraseña incorrectos.")
        else:
            messages.error(request, "Correo o contraseña incorrectos.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


# Vista para el cierre de sesión
def logout_view(request):
    logout(request)
    return redirect('login')


# Vista para la página de inicio de administración
@login_required
@user_passes_test(is_administracion)
def inicio_administracion(request):
    return render(request, 'administracion/inicio_administracion.html')


# Vista para listar operadores
@login_required
@user_passes_test(is_administracion)
def operadores(request):
    operadores = Operador.objects.all().order_by('nombre')
    paginator = Paginator(operadores, 2)
    page_number = request.GET.get('page')
    operadores = paginator.get_page(page_number)
    return render(request, 'administracion/operadores/index_operador.html', {'operadores': operadores})


# Vista para crear un operador
@login_required
@user_passes_test(is_administracion)
def crear_operador(request):
    if request.method == "POST":
        formulario = OperadorForm(request.POST, request.FILES)
        if formulario.is_valid():
            formulario.save()
            return redirect('operadores')
    else:
        formulario = OperadorForm()
    return render(request, 'administracion/operadores/crear_operador.html', {'formulario': formulario})


# Vista para editar un operador
@login_required
@user_passes_test(is_administracion)
def editar_operador(request, cedula):
    operador = get_object_or_404(Operador, cedula=cedula)
    if request.method == "POST":
        formulario = OperadorForm(request.POST, request.FILES, instance=operador)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, f"Operador {operador.nombre} {operador.apellido} actualizado correctamente.")
            return redirect('operadores')
    else:
        formulario = OperadorForm(instance=operador)
    return render(request, 'administracion/operadores/editar_operador.html', {
        'formulario': formulario,
        'operador': operador
    })


# Vista para borrar un operador
@login_required
@user_passes_test(is_administracion)
def borrar_operador(request, cedula):
    operador = get_object_or_404(Operador, cedula=cedula)
    if Asignacion.objects.filter(operador=operador).exists():
        messages.error(request, f"El operador {operador.nombre} {operador.apellido} (Cédula: {operador.cedula}) no puede ser eliminado porque tiene asignaciones registradas.")
        return redirect('operadores')
    try:
        operador.delete()
        messages.success(request, f"Operador {operador.nombre} {operador.apellido} eliminado correctamente.")
    except Exception as e:
        messages.error(request, f"Error al eliminar el operador {operador.nombre} {operador.apellido}: {str(e)}")
    return redirect('operadores')


# Vista para listar vehículos
@login_required
@user_passes_test(is_administracion)
def vehiculos(request):
    vehiculos = Vehiculo.objects.all().order_by('modelo')
    paginator = Paginator(vehiculos, 2)
    page_number = request.GET.get('page')
    vehiculos = paginator.get_page(page_number)
    return render(request, 'administracion/vehiculos/index_vehiculo.html', {'vehiculos': vehiculos})


# Vista para crear un vehículo
@login_required
@user_passes_test(is_administracion)
def crear_vehiculo(request):
    if request.method == "POST":
        formulario = VehiculoForm(request.POST, request.FILES)
        if formulario.is_valid():
            formulario.save()
            return redirect('vehiculos')
    else:
        formulario = VehiculoForm()
    return render(request, 'administracion/vehiculos/crear_vehiculo.html', {'formulario': formulario})


# Vista para crear una marca y modelo
@login_required
@user_passes_test(is_administracion)
@require_POST
def crear_modelo_marca(request):
    try:
        data = json.loads(request.body)
        marca_nombre = data.get('marca', '').strip()
        modelo_nombre = data.get('modelo', '').strip()
        if not marca_nombre or not modelo_nombre:
            return JsonResponse({'success': False, 'errors': 'La marca y el modelo no pueden estar vacíos.'}, status=400)
        marca_obj, created = Marca.objects.get_or_create(
            nombre__iexact=marca_nombre, 
            defaults={'nombre': marca_nombre.capitalize()}
        )
        if Modelo.objects.filter(marca=marca_obj, nombre__iexact=modelo_nombre).exists():
            return JsonResponse({'success': False, 'errors': 'Este modelo ya existe para esta marca.'}, status=400)
        nuevo_modelo = Modelo.objects.create(marca=marca_obj, nombre=modelo_nombre.capitalize())
        return JsonResponse({
            'success': True,
            'id': nuevo_modelo.id,
            'marca': marca_obj.nombre,
            'modelo': nuevo_modelo.nombre
        })
    except Exception as e:
        return JsonResponse({'success': False, 'errors': str(e)}, status=500)


# Vista para editar un vehículo
@login_required
@user_passes_test(is_administracion)
def editar_vehiculo(request, placa):
    vehiculo = get_object_or_404(Vehiculo, placa=placa)
    if Asignacion.objects.filter(vehiculo=vehiculo).exists():
        messages.error(request, f"El vehículo con placa {vehiculo.placa} no puede ser editado porque tiene asignaciones registradas.")
        return redirect('vehiculos')
    if request.method == 'POST':
        formulario = VehiculoForm(request.POST, request.FILES, instance=vehiculo)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, f"Vehículo con placa {vehiculo.placa} actualizado correctamente.")
            return redirect('vehiculos')
    else:
        formulario = VehiculoForm(instance=vehiculo)
    return render(request, 'administracion/vehiculos/editar_vehiculo.html', {'formulario': formulario, 'vehiculo': vehiculo})


# Vista para borrar un vehículo
@login_required
@user_passes_test(is_administracion)
def borrar_vehiculo(request, placa):
    vehiculo = get_object_or_404(Vehiculo, placa=placa)
    if Asignacion.objects.filter(vehiculo=vehiculo).exists():
        messages.error(request, f"El vehículo con placa {vehiculo.placa} no puede ser eliminado porque tiene asignaciones registradas.")
        return redirect('vehiculos')
    try:
        vehiculo.delete()
        messages.success(request, f"Vehículo con placa {vehiculo.placa} eliminado correctamente.")
    except Exception as e:
        messages.error(request, f"Error al eliminar el vehículo {vehiculo.placa}: {str(e)}")
    return redirect('vehiculos')


# Vista para descargar el código QR de un vehículo
@login_required
@user_passes_test(is_administracion)
def descargar_qr(request, placa):
    try:
        placa_vehiculo = Vehiculo.objects.get(placa=placa)
        qr_path = os.path.join(settings.MEDIA_ROOT, placa_vehiculo.codigo_qr.name)
        return FileResponse(open(qr_path, 'rb'), as_attachment=True, filename=os.path.basename(qr_path))
    except (Vehiculo.DoesNotExist, FileNotFoundError):
        raise Http404("El QR no existe.")


# Vista para listar asignaciones
@login_required
@user_passes_test(is_administracion)
def asignaciones(request):
    asignaciones = Asignacion.objects.all().order_by('id')
    paginator = Paginator(asignaciones, 2)
    page_number = request.GET.get('page')
    asignaciones = paginator.get_page(page_number)
    return render(request, 'administracion/asignaciones/index_asignacion.html', {'asignaciones': asignaciones})


# Vista para crear una asignación
@login_required
@user_passes_test(is_administracion)
def crear_asignacion(request):
    if request.method == 'POST':
        formulario = AsignacionForm(request.POST)
        if formulario.is_valid():
            operador_seleccionado = formulario.cleaned_data['operador']
            vehiculo_seleccionado = formulario.cleaned_data['vehiculo']
            tipo_material_seleccionado = formulario.cleaned_data.get('tipo_material')
            fecha_actual = timezone.localtime(timezone.now()).date()
            otras_asignaciones_activas_operador = Asignacion.objects.filter(
                operador=operador_seleccionado,
                estado=True,
                fecha_asignacion=fecha_actual
            ).exclude(vehiculo=vehiculo_seleccionado)
            if otras_asignaciones_activas_operador.exists():
                messages.error(request, f"El operador {operador_seleccionado} ya tiene una asignación activa con otro vehículo para hoy ({otras_asignaciones_activas_operador.first().vehiculo.placa}).")
                return render(request, 'administracion/asignaciones/crear_asignacion.html', {
                    'formulario': formulario,
                    'operadores': Operador.objects.all(),
                    'vehiculos': Vehiculo.objects.all(),
                    'tipos_material': TipoMaterial.objects.all()
                })
            otras_asignaciones_activas_vehiculo = Asignacion.objects.filter(
                vehiculo=vehiculo_seleccionado,
                estado=True,
                fecha_asignacion=fecha_actual
            ).exclude(operador=operador_seleccionado)
            if otras_asignaciones_activas_vehiculo.exists():
                messages.error(request, f"El vehículo {vehiculo_seleccionado} ya tiene una asignación activa con otro operador para hoy ({otras_asignaciones_activas_vehiculo.first().operador}).")
                return render(request, 'administracion/asignaciones/crear_asignacion.html', {
                    'formulario': formulario,
                    'operadores': Operador.objects.all(),
                    'vehiculos': Vehiculo.objects.all(),
                    'tipos_material': TipoMaterial.objects.all()
                })
            asignacion_existente, created = Asignacion.objects.get_or_create(
                operador=operador_seleccionado,
                vehiculo=vehiculo_seleccionado,
                fecha_asignacion=fecha_actual,
                defaults={
                    'tipo_material': tipo_material_seleccionado,
                    'estado': True,
                    'total_vueltas': 0,
                }
            )
            if not created:
                if asignacion_existente.estado:
                    messages.warning(request, f"La asignación para el operador {operador_seleccionado} y el vehículo {vehiculo_seleccionado} ya está activa para hoy.")
                else:
                    asignacion_existente.estado = True
                    asignacion_existente.tipo_material = tipo_material_seleccionado
                    asignacion_existente.total_vueltas = 0
                    asignacion_existente.save()
                    messages.success(request, f"La asignación existente para {operador_seleccionado} y {vehiculo_seleccionado} ha sido reactivada y actualizada para hoy.")
            else:
                messages.success(request, "Nueva asignación creada exitosamente.")
            
            return redirect('asignaciones')
        else:
            messages.error(request, "Por favor, corrige los errores en el formulario.")
    else:
        formulario = AsignacionForm()
    return render(request, 'administracion/asignaciones/crear_asignacion.html', {
        'formulario': formulario,
        'operadores': Operador.objects.all(),
        'vehiculos': Vehiculo.objects.all(),
        'tipos_material': TipoMaterial.objects.all()
    })


# Vista para crear un tipo de material
@login_required
@user_passes_test(is_administracion)
def crear_tipo_material(request):
    if request.method == "POST":
        data = json.loads(request.body)
        nombre = data.get("nombre", "").strip()
        if nombre:
            material, creado = TipoMaterial.objects.get_or_create(nombre=nombre)
            return JsonResponse({"success": True, "id": material.id, "nombre": material.nombre})
    return JsonResponse({"success": False})


# Vista para editar una asignación
@login_required
@user_passes_test(is_administracion)
def editar_asignacion(request, id):
    asignacion = get_object_or_404(Asignacion, id=id)
    if asignacion.total_vueltas > 0:
        messages.error(request, f"La asignación ID {asignacion.id} no puede ser editada porque tiene {asignacion.total_vueltas} vuelta(s) registrada(s). Para editar, el total de vueltas debe ser cero.")
        return redirect('asignaciones')
    if request.method == 'POST':
        formulario = AsignacionForm(request.POST, instance=asignacion)
        if formulario.is_valid():
            formulario.save()
            messages.success(request, f"Asignación ID {asignacion.id} actualizada correctamente.")
            return redirect('asignaciones')
    else:
        formulario = AsignacionForm(instance=asignacion)
    return render(request, 'administracion/asignaciones/editar_asignacion.html', {'formulario': formulario, 'asignacion': asignacion})


# Vista para borrar una asignación
@login_required
@user_passes_test(is_administracion)
def borrar_asignacion(request, id):
    asignacion = get_object_or_404(Asignacion, id=id)
    if asignacion.total_vueltas > 0:
        messages.error(request, f"La asignación ID {asignacion.id} no puede ser eliminada porque tiene {asignacion.total_vueltas} vuelta(s) registrada(s). Para eliminar, el total de vueltas debe ser cero.")
        return redirect('asignaciones')
    try:
        asignacion.delete()
        messages.success(request, f"Asignación ID {asignacion.id} eliminada correctamente.")
    except Exception as e:
        messages.error(request, f"Error al eliminar la asignación ID {asignacion.id}: {str(e)}")
    return redirect('asignaciones')


# Vista para cambiar el estado de una asignación
@login_required
@user_passes_test(is_administracion)
def cambiar_estado(request, id):
    asignacion = get_object_or_404(Asignacion, id=id)
    asignacion.estado = not asignacion.estado
    asignacion.save()
    return redirect('asignaciones')


# Vista para registrar una vuelta
@login_required
@user_passes_test(is_administracion)
def registrar_vuelta(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            placa_escaneada_encriptada = data.get("placa")
            if not placa_escaneada_encriptada:
                return JsonResponse({"error": "No se proporcionó la placa desde el QR."}, status=400)
            try:
                key = settings.FERNET_KEY
            except AttributeError:
                return JsonResponse({"error": "Error de configuración interna del servidor."}, status=500)
            f = Fernet(key)
            try:
                placa_encriptada_bytes = placa_escaneada_encriptada.encode('utf-8')
                placa_original_bytes = f.decrypt(placa_encriptada_bytes)
                placa_original_str = placa_original_bytes.decode('utf-8')
            except InvalidToken:
                return JsonResponse({"error": "Código QR inválido o no reconocido."}, status=400)
            except Exception:
                return JsonResponse({"error": "Error al procesar la información del código QR."}, status=400)
            vehiculo = Vehiculo.objects.get(placa=placa_original_str)
            fecha_hoy = timezone.localdate()
            try:
                relacion = Asignacion.objects.get(
                    vehiculo=vehiculo, 
                    estado=True,
                    fecha_asignacion=fecha_hoy
                )
            except Asignacion.DoesNotExist:
                return JsonResponse({
                    "error": f"No se encontró una asignación activa para el vehículo {placa_original_str} en la fecha de hoy ({fecha_hoy.strftime('%d-%m-%Y')})."
                }, status=404)
            except Asignacion.MultipleObjectsReturned:
                return JsonResponse({
                    "error": f"Múltiples asignaciones activas encontradas para el vehículo {placa_original_str} hoy. Por favor, contacte al administrador."
                }, status=500)
            if relacion.ultima_vuelta_registrada_en:
                ahora = timezone.now()
                tiempo_desde_ultima_vuelta = ahora - relacion.ultima_vuelta_registrada_en
                if tiempo_desde_ultima_vuelta < timedelta(minutes=10):
                    minutos_restantes = 10 - int(tiempo_desde_ultima_vuelta.total_seconds() / 60)
                    segundos_restantes = 60 - int(tiempo_desde_ultima_vuelta.total_seconds() % 60)
                    if segundos_restantes == 60:
                        segundos_restantes = 0
                        if minutos_restantes < 10:
                             minutos_restantes +=1
                    if tiempo_desde_ultima_vuelta.total_seconds() > 0 and segundos_restantes == 0 and minutos_restantes > 0:
                        minutos_reales_espera = 9 - int(tiempo_desde_ultima_vuelta.total_seconds() // 60)
                        segundos_reales_espera = 59 - int(tiempo_desde_ultima_vuelta.total_seconds() % 60)
                    else:
                        minutos_reales_espera = 9 - int(tiempo_desde_ultima_vuelta.total_seconds() // 60)
                        segundos_reales_espera = 59 - int(tiempo_desde_ultima_vuelta.total_seconds() % 60)
                        if segundos_reales_espera < 0:
                            segundos_reales_espera = 0
                    return JsonResponse({
                        "error": (f"Este vehículo ya registró una vuelta hace menos de 10 minutos. "
                                  f"Intente de nuevo en aproximadamente {minutos_reales_espera} min y {segundos_reales_espera} seg.")
                    }, status=429)
            relacion.total_vueltas += 1
            relacion.ultima_vuelta_registrada_en = timezone.now()
            relacion.save() 
            return JsonResponse({
                "message": "Vuelta registrada con éxito.",
                "total_vueltas": relacion.total_vueltas,
                "total_material_acumulado": float(relacion.total_material)
            }, status=200)
        except Vehiculo.DoesNotExist:
            return JsonResponse({"error": "Vehículo no encontrado con la placa proporcionada por el QR."}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Solicitud JSON mal formada."}, status=400)
        except Exception as e:
            return JsonResponse({"error": "Ocurrió un error inesperado en el servidor al registrar la vuelta."}, status=500)
    return JsonResponse({"error": "Método no permitido."}, status=405)


# Vista para enviar el código QR de un vehículo por correo electrónico
@login_required
@user_passes_test(is_administracion)
def enviar_qr_correo(request, placa):
    vehiculo = get_object_or_404(Vehiculo, placa=placa)
    if request.method == 'POST':
        correo_destino = request.POST.get('correo')
        if not correo_destino:
            messages.error(request, 'No se proporcionó una dirección de correo válida.')
            return JsonResponse({'message': 'No se proporcionó una dirección de correo válida.'}, status=400)
        nombre_completo_operador = "Operador"
        try:
            operador = Operador.objects.get(correo__iexact=correo_destino)
            nombre_completo_operador = f"{operador.nombre} {operador.apellido}"
        except Operador.DoesNotExist:
            pass
        if vehiculo.codigo_qr and vehiculo.codigo_qr.file:
            subject = f"Código QR del vehículo {vehiculo.placa} - ARPETA"
            html_content = render_to_string('administracion/correo_qr.html', {
                'vehiculo': vehiculo,
                'nombre_operador': nombre_completo_operador
            })
            email = EmailMessage(
                subject,
                html_content,
                settings.DEFAULT_FROM_EMAIL,
                [correo_destino],
            )
            email.content_subtype = "html"
            qr_file_path = vehiculo.codigo_qr.path 
            try:
                email.attach_file(qr_file_path, mimetype='image/png')
                email.send(fail_silently=False)
                messages.success(request, '¡El código QR se envió por correo exitosamente!')
                return JsonResponse({'message': 'Correo enviado exitosamente!'})
            except FileNotFoundError:
                messages.error(request, 'Error: El archivo QR no se encontró en el servidor.')
                return JsonResponse({'message': 'Error: El archivo QR no se encontró en el servidor.'}, status=500)
            except Exception as e:
                messages.error(request, f'Error al enviar el correo: {e}')
                print(f"Error al enviar correo para {vehiculo.placa} a {correo_destino}: {e}")
                return JsonResponse({'message': f'Error al enviar el correo: {e}'}, status=500)
        else:
            messages.error(request, 'El vehículo no tiene un código QR asociado.')
            return JsonResponse({'message': 'El vehículo no tiene código QR.'}, status=400)
    else:
        messages.warning(request, 'Acceso no permitido.')
        return JsonResponse({'message': 'Método no permitido.'}, status=405)


# --------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------

# Vista para la página de inicio de gerente
@user_passes_test(is_gerente)
@login_required
def inicio_gerente(request):
    return render(request, 'gerente/inicio_gerente.html')

# Vista para la página de pagos del gerente
@user_passes_test(is_gerente)
def pagos_gerente(request):
    return render(request, 'gerente/pagos_gerente.html')

# Vista para la página de reportes del gerente
# views.py (nueva vista para el reporte)
from django.db.models import Sum, Count, F, FloatField, ExpressionWrapper
from django.db.models.functions import TruncMonth, ExtractHour
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
import json
from datetime import datetime, timedelta
from django.db.models import Avg

@login_required
@user_passes_test(is_gerente)
def reportes_gerente(request):
    # Datos de Operadores
    operadores = Operador.objects.all()
    total_operadores = operadores.count()
    operadores_activos = operadores.filter(activo=True).count()
    operadores_inactivos = total_operadores - operadores_activos
    operadores_independientes = operadores.filter(independiente=True).count()
    operadores_no_independientes = total_operadores - operadores_independientes

    # Datos de Vehículos
    vehiculos = Vehiculo.objects.all()
    total_vehiculos = vehiculos.count()
    vehiculos_activos = vehiculos.filter(activo=True).count()
    vehiculos_mantenimiento = total_vehiculos - vehiculos_activos
    porcentaje_disponibilidad = round((vehiculos_activos / total_vehiculos * 100) if total_vehiculos > 0 else 0)

    # Cálculo de capacidad promedio de vehículos
   

    # Datos de Asignaciones
    volumen_expr = ExpressionWrapper(
        F('total_vueltas') * F('vehiculo__alto') * F('vehiculo__ancho') * F('vehiculo__largo'),
        output_field=FloatField()
    )
    
    asignaciones = Asignacion.objects.all()
    total_asignaciones = asignaciones.count()
    asignaciones_activas = asignaciones.filter(estado=True).count()
    asignaciones_inactivas = total_asignaciones - asignaciones_activas
    
    total_material_qs = asignaciones.annotate(total_material=volumen_expr)\
                                   .aggregate(Sum('total_material'))
    total_material = total_material_qs['total_material__sum'] or 0

    # Asignaciones recientes (últimas 5)
    asignaciones_recientes = asignaciones.select_related('operador', 'vehiculo', 'tipo_material')\
                                       .order_by('-fecha_asignacion')[:5]

    # Gráfico de actividad por hora
    horas = range(6, 21, 2)  # De 6am a 8pm cada 2 horas
    horas_labels = [f"{h}:00-{h+2}:00" for h in horas[:-1]]
    actividad_horaria = []
    
    for h in horas[:-1]:
        count = asignaciones.filter(
            ultima_vuelta_registrada_en__hour__gte=h,
            ultima_vuelta_registrada_en__hour__lt=h+2
        ).count()
        actividad_horaria.append(count)

    context = {
        # Operadores
        'total_operadores': total_operadores,
        'operadores_activos': operadores_activos,
        'operadores_inactivos': operadores_inactivos,
        'operadores_independientes': operadores_independientes,
        'operadores_no_independientes': operadores_no_independientes,
        
        # Vehículos
        'total_vehiculos': total_vehiculos,
        'vehiculos_activos': vehiculos_activos,
        'vehiculos_mantenimiento': vehiculos_mantenimiento,
        'porcentaje_disponibilidad': porcentaje_disponibilidad,
        
        
        # Asignaciones
        'total_asignaciones': total_asignaciones,
        'asignaciones_activas': asignaciones_activas,
        'asignaciones_inactivas': asignaciones_inactivas,
        'total_material': round(total_material, 2),
        'asignaciones_recientes': asignaciones_recientes,
        
        # Gráficos
        'horas_labels': json.dumps(horas_labels),
        'actividad_horaria': json.dumps(actividad_horaria),
        
        # Fecha de generación
        'fecha_generacion': datetime.now().strftime("%d/%m/%Y %H:%M")
    }

    if 'pdf' in request.GET:
        return generar_pdf_reporte(context)
    
    return render(request, 'gerente/reportes_gerente.html', context)

def generar_pdf_reporte(context):
    template = get_template('gerente/gerente_reporte_pdf.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reportes_gerente.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error al generar PDF', status=500)
    return response

# Vista para ver todos los detalles de un operador
@login_required
@user_passes_test(is_administracion)
def detalles_operador(request, cedula):
    try:
        operador = Operador.objects.get(cedula=cedula)
        
        data = {
            'cedula': operador.cedula,
            'nombre': operador.nombre,
            'apellido': operador.apellido,
            'telefono': str(operador.telefono),
            'correo': operador.correo or 'No especificado',
            'direccion': operador.direccion or 'No especificada',
            'independiente_texto': 'Sí' if operador.independiente else 'No',
            'foto_operador': operador.foto_operador.url if operador.foto_operador else None,
        }
        return JsonResponse(data)

    except Operador.DoesNotExist:
        return JsonResponse({'error': 'Operador no encontrado'}, status=404)

#---------------------------------------------Gerente---------------------------------------------------------------------------
@user_passes_test(is_gerente)
def base_gerente(request):
    return render(request, 'gerente/base_gerente.html')

@user_passes_test(is_gerente)
def lista_asignaciones (request):
    return render(request, 'gerente/lista_asignaciones.html')


#------------------------------------------------------Operadores Gerente-----------------------------------------------------------------
from django.shortcuts import render
from django.views import View
from .models import Operador, Asignacion, Vehiculo
from django.db.models import Count, Q
import plotly.express as px
import pandas as pd
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
import pandas as pd
import plotly.express as px
from django.db.models import Count
from .models import Operador, Asignacion  # Ajusta el import según tu estructura

class OperadoresGerenteView(View):
    template_name = 'gerente/operadores_gerente.html'

    def get(self, request):
        # Obtenemos todos los operadores para la tabla (sin orden por fecha)
        operadores = Operador.objects.all()

        # Estadísticas básicas
        total_operadores = operadores.count()
        operadores_activos = operadores.filter(activo=True).count()
        operadores_inactivos = total_operadores - operadores_activos

        # Operadores con asignaciones activas
        asignaciones_activas = Asignacion.objects.filter(estado=True).select_related('operador', 'vehiculo')

        # Gráfico de Estado de operadores
        estado_data = {
            'Estado': ['Activos', 'Inactivos'],
            'Cantidad': [operadores_activos, operadores_inactivos]
        }
        fig_estado = px.pie(
            estado_data,
            values='Cantidad',
            names='Estado',
            title='Distribución de Operadores por Estado',
            color_discrete_sequence=['#4CAF50', '#F44336']
        )
        fig_estado.update_traces(
            textposition='inside',
            textinfo='percent+label',
            marker=dict(line=dict(color='#FFFFFF', width=1))
        )
        grafico_estado = fig_estado.to_html(full_html=False)

        # Gráfico de Tipo de operadores
        operadores_independientes = operadores.filter(independiente=True).count()
        operadores_no_independientes = total_operadores - operadores_independientes

        tipo_data = {
            'Tipo': ['Independientes', 'No Independientes'],
            'Cantidad': [operadores_independientes, operadores_no_independientes]
        }
        fig_tipo = px.bar(
            tipo_data,
            x='Tipo',
            y='Cantidad',
            title='Distribución por Tipo de Operador',
            color='Tipo',
            color_discrete_sequence=['#2196F3', '#9C27B0']
        )
        fig_tipo.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title=None,
            yaxis_title='Cantidad'
        )
        grafico_tipo = fig_tipo.to_html(full_html=False)

        # Gráfico de Vehículos más asignados (si hay)
        vehiculos_populares = Asignacion.objects.values(
            'vehiculo__placa', 'vehiculo__modelo__marca__nombre', 'vehiculo__modelo__nombre'
        ).annotate(
            total_asignaciones=Count('id')
        ).order_by('-total_asignaciones')[:5]

        grafico_vehiculos = None
        if vehiculos_populares:
            df_vehiculos = pd.DataFrame(list(vehiculos_populares))
            df_vehiculos['vehiculo'] = df_vehiculos.apply(
                lambda x: f"{x['vehiculo__placa']} ({x['vehiculo__modelo__marca__nombre']} {x['vehiculo__modelo__nombre']})",
                axis=1
            )
            fig_vehiculos = px.bar(
                df_vehiculos,
                x='vehiculo',
                y='total_asignaciones',
                title='Vehículos más asignados',
                labels={'total_asignaciones': 'N° de Asignaciones', 'vehiculo': 'Vehículo'},
                color_discrete_sequence=['#607D8B']
            )
            fig_vehiculos.update_layout(
                xaxis_title=None,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            grafico_vehiculos = fig_vehiculos.to_html(full_html=False)

        context = {
            'operadores': operadores,
            'total_operadores': total_operadores,
            'operadores_activos': operadores_activos,
            'operadores_inactivos': operadores_inactivos,
            'operadores_independientes': operadores_independientes,
            'operadores_no_independientes': operadores_no_independientes,
            'asignaciones_activas': asignaciones_activas,
            'grafico_estado': grafico_estado,
            'grafico_tipo': grafico_tipo,
            'grafico_vehiculos': grafico_vehiculos,
        }

        if 'pdf' in request.GET:
            return self.generate_pdf(context)

        return render(request, self.template_name, context)

    def generate_pdf(self, context):
        template = get_template('gerente/operadores_gerente_pdf.html')
        html = template.render(context)

        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

        if not pdf.err:
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="reporte_operadores.pdf"'
            return response

        return HttpResponse('Error al generar el PDF', status=400)
    
    
#----------------------------------------------------Vehiculos Gerente-------------------------------------------------------------    
from django.views import View
from django.db.models import Sum
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models.functions import ExtractMonth
import json
from .models import  Vehiculo, Asignacion  # Asegúrate de importar tu modelo de vueltas

class VehiculosGerenteView(View):
    template_name = 'gerente/vehiculos_gerente.html'
    paginate_by = 10

    def get(self, request):
        # Filtros y búsqueda
        search_query = request.GET.get('search', '')
        estado_filter = request.GET.get('estado', None)

        # Datos básicos
        total_vehiculos = Vehiculo.objects.count()
        vehiculos_activos = Vehiculo.objects.filter(activo=True).count()
        vehiculos_mantenimiento = total_vehiculos - vehiculos_activos

        # Asignaciones activas
        asignaciones_qs = Asignacion.objects.filter(estado=True)\
            .select_related('vehiculo', 'vehiculo__modelo', 'vehiculo__modelo__marca', 'operador')\
            .order_by('-ultima_vuelta_registrada_en')

        if search_query:
            asignaciones_qs = asignaciones_qs.filter(
                Q(vehiculo__placa__icontains=search_query) |
                Q(operador__nombre__icontains=search_query) |
                Q(operador__apellido__icontains=search_query) |
                Q(vehiculo__modelo__nombre__icontains=search_query) |
                Q(vehiculo__modelo__marca__nombre__icontains=search_query)
            )

        if estado_filter:
            asignaciones_qs = asignaciones_qs.filter(estado=(estado_filter == 'activo'))

        # Paginación
        paginator = Paginator(asignaciones_qs, self.paginate_by)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Datos reales para gráficos (implementa estos métodos según tus modelos)
        dias_semana, vueltas_diarias = self.get_vueltas_ultima_semana()
        meses_anio, vueltas_mensuales = self.get_vueltas_ultimo_anio()
        horas_dia, vueltas_horarias = self.get_vueltas_por_hora()

        context = {
            # Totales
            'total_vehiculos': total_vehiculos,
            'vehiculos_activos': vehiculos_activos,
            'vehiculos_mantenimiento': vehiculos_mantenimiento,
            'porcentaje_disponibilidad': round((vehiculos_activos / total_vehiculos * 100) if total_vehiculos > 0 else 0),
            'tiempo_promedio_mantenimiento': 3,
            
            # Asignaciones
            'asignaciones_activas': page_obj,
            'total_asignaciones_activas': asignaciones_qs.count(),
            
            # ... otros datos ...
            'dias_semana': dias_semana,  # Sin json.dumps
            'vueltas_diarias': vueltas_diarias,
            'meses_anio': meses_anio,
            'vueltas_mensuales': vueltas_mensuales,
            'horas_dia': horas_dia,
            'vueltas_horarias': vueltas_horarias,
       
                    
            # Filtros
            'search_query': search_query,
            'estado_filter': estado_filter,
        }
        
        return render(request, "gerente/vehiculos_gerente.html", context)

    def get_vueltas_ultima_semana(self):
        """Obtiene vueltas de los últimos 7 días basado en las asignaciones"""
        hoy = timezone.now().date()
        dias = []
        vueltas = []
        
        for i in range(6, -1, -1):
            fecha = hoy - timedelta(days=i)
            dias.append(fecha.strftime('%a'))  # Nombre corto del día (Lun, Mar, etc.)
            
            # Sumamos el total_vueltas de las asignaciones que tuvieron actividad ese día
            total = Asignacion.objects.filter(
                ultima_vuelta_registrada_en__date=fecha
            ).aggregate(total=Sum('total_vueltas'))['total'] or 0
            
            vueltas.append(total)
        
        return dias, vueltas

    def get_vueltas_ultimo_anio(self):
        año_actual = timezone.now().year

        qs = Asignacion.objects.filter(
            ultima_vuelta_registrada_en__year=año_actual
        ).annotate(
            mes=ExtractMonth('ultima_vuelta_registrada_en')
        ).values('mes').annotate(
            total=Sum('total_vueltas')
        )
        resultados = {entry['mes']: entry['total'] for entry in qs}

        meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 
                'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        vueltas = [resultados.get(mes, 0) for mes in range(1, 13)]
        return meses, vueltas

    def get_vueltas_por_hora(self):
        """Obtiene vueltas por franja horaria basado en asignaciones"""
        horas = ['6-8', '8-10', '10-12', '12-14', '14-16', '16-18', '18-20']
        vueltas = []
        
        for rango in [(6,8), (8,10), (10,12), (12,14), (14,16), (16,18), (18,20)]:
            # Sumamos el total_vueltas de asignaciones con actividad en esa franja
            total = Asignacion.objects.filter(
                ultima_vuelta_registrada_en__hour__gte=rango[0],
                ultima_vuelta_registrada_en__hour__lt=rango[1]
            ).aggregate(total=Sum('total_vueltas'))['total'] or 0
            
            vueltas.append(total)
        
        return horas, vueltas
        
 #--------------------------------------------------------Asignaciones Gerente------------------------------------------------------       
  
from django.shortcuts import render
from django.db.models import Sum, Count, F, FloatField, ExpressionWrapper
from django.db.models.functions import TruncMonth
from .models import Asignacion, TipoMaterial

def dashboard_asignaciones(request):
    total_asignaciones = Asignacion.objects.count()
    asignaciones_activas = Asignacion.objects.filter(estado=True).count()
    asignaciones_inactivas = Asignacion.objects.filter(estado=False).count()

    # Calcular total de material usando alto * ancho * largo
    volumen_expr = ExpressionWrapper(
        F('total_vueltas') * F('vehiculo__alto') * F('vehiculo__ancho') * F('vehiculo__largo'),
        output_field=FloatField()
    )

    total_material_qs = Asignacion.objects.annotate(total_material=volumen_expr)\
                                          .aggregate(Sum('total_material'))
    total_material = total_material_qs['total_material__sum'] or 0

    # Datos para gráfico de Material por Tipo
    materiales = TipoMaterial.objects.all()
    tipos_material_labels = [m.nombre for m in materiales]
    tipos_material_data = [
        Asignacion.objects
        .filter(tipo_material=m)
        .annotate(total_material=volumen_expr)
        .aggregate(Sum('total_material'))['total_material__sum'] or 0
        for m in materiales
    ]

    # Datos para gráfico de Asignaciones por Mes
    asignaciones_por_mes = (
        Asignacion.objects
        .annotate(mes=TruncMonth('fecha_asignacion'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )

    meses_labels = [a['mes'].strftime('%b %Y') for a in asignaciones_por_mes]
    meses_data = [a['total'] for a in asignaciones_por_mes]

    # Asignaciones recientes
    asignaciones_recientes = Asignacion.objects.select_related('operador', 'vehiculo', 'tipo_material')\
                                               .order_by('-fecha_asignacion')[:10]

    context = {
        'total_asignaciones': total_asignaciones,
        'asignaciones_activas': asignaciones_activas,
        'asignaciones_inactivas': asignaciones_inactivas,
        'total_material': total_material,
        'tipos_material_labels': tipos_material_labels,
        'tipos_material_data': tipos_material_data,
        'meses_labels': meses_labels,
        'meses_data': meses_data,
        'asignaciones_recientes': asignaciones_recientes,
    }

    return render(request, 'gerente/asignaciones_gerente.html', context)

#----------------------------------------------------Nomina---------------------------------------------------------------------

@user_passes_test(is_nomina)
def base_nomina (request):
    return render(request, 'nomina/base_nomina')

@user_passes_test(is_nomina)
def pagos_nomina (request):
    return render(request, 'nomina/pagos_nomina')

@user_passes_test(is_nomina)
def inicio_nomina (request):
    return render(request, 'nomina/inicio_nomina.html')

#----------------------------------------------------------Calcular Pago-----------------------------------------------------------
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from datetime import datetime
from .models import Asignacion

def calcular_pago(request):
    asignaciones_activas = Asignacion.objects.filter(estado=True)
    
    if request.method == 'POST':
        try:
            asignacion_id = request.POST.get('asignacion')
            tipo_pago = request.POST.get('tipo_pago')
            confirmar = request.POST.get('confirmar', False)
            
            if not asignacion_id or not tipo_pago:
                messages.error(request, "Debe completar todos los campos del formulario")
                return redirect('calcular_pago')
                
            if not confirmar:
                messages.error(request, "Debe confirmar que los datos son correctos")
                return redirect('calcular_pago')
            
            asignacion = Asignacion.objects.get(pk=asignacion_id, estado=True)
            
            if asignacion.total_vueltas < 16:
                messages.error(request, f"El operador no ha completado las 16 vueltas mínimas. Vueltas actuales: {asignacion.total_vueltas}")
                return redirect('calcular_pago')
            
            capacidad_camion = float(asignacion.vehiculo.capacidad_carga)
            material = asignacion.tipo_material.nombre.lower() if asignacion.tipo_material else "arena"
            
            pago_arena = capacidad_camion
            
            if material in ['arena', 'gravilla']:
                tasa = 12
            elif material in ['gravilla', 'granzon']:
                tasa = 4
            else:  # polvillo
                tasa = 2
                
            pago_divisas = capacidad_camion * tasa
            
            context = {
                'asignacion': asignacion,
                'tipo_pago': tipo_pago,
                'pago_arena': pago_arena,
                'pago_divisas': pago_divisas,
                'material': material,
                'tasa': tasa,
                'fecha': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                'capacidad_camion': capacidad_camion,
            }
            
            if 'generar_pdf' in request.POST:
                return generar_recibo_pdf(request, context)
            
            return render(request, 'nomina/resultado_pago.html', context)
            
        except Asignacion.DoesNotExist:
            messages.error(request, "La asignación seleccionada no es válida")
            return redirect('calcular_pago')
        except Exception as e:
            messages.error(request, f"Ocurrió un error: {str(e)}")
            return redirect('calcular_pago')
    
    return render(request, 'nomina/calcular_pago.html', {
        'asignaciones': asignaciones_activas
    })
    
    #------------------------------------------------Generar Recibo--------------------------------------------------------------------

def generar_recibo_pdf(request, context=None, asignacion_id=None):
    if context is None:
        try:
            asignacion = Asignacion.objects.get(id=asignacion_id)
            
            capacidad_camion = float(asignacion.vehiculo.capacidad_carga)
            material = asignacion.tipo_material.nombre.lower() if asignacion.tipo_material else "arena"
            
            if material in ['arena', 'gravilla']:
                tasa = 12
            elif material in ['gravilla', 'granzon']:
                tasa = 4
            else:
                tasa = 2
                
            context = {
                'asignacion': asignacion,
                'tipo_pago': request.GET.get('tipo_pago', 'arena'),
                'pago_arena': capacidad_camion,
                'pago_divisas': capacidad_camion * tasa,
                'material': material,
                'tasa': tasa,
                'fecha': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                'capacidad_camion': capacidad_camion,
            }
        except Asignacion.DoesNotExist:
            messages.error(request, "La asignación no existe")
            return redirect('calcular_pago')
    
    template = get_template('nomina/recibo_pago.html')
    html = template.render(context)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="recibo_pago_{context["asignacion"].operador.cedula}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error al generar PDF')
    return response

#------------------------------------------------------------Resumen del pago-------------------------------------------------------------

from django.shortcuts import render, redirect
from .models import Asignacion
from django.core.exceptions import ValidationError

def PagoOperadorForm(request):
    error_messages = []
    asignacion = None
    tipo_pago = None
    confirmado = False

    if request.method == 'POST':
        # Obtener datos del POST
        asignacion_id = request.POST.get('asignacion')
        tipo_pago = request.POST.get('tipo_pago')
        confirmar = request.POST.get('confirmar') == 'on'  # Los checkboxes envían 'on' cuando están marcados

        # Validación manual
        if not asignacion_id:
            error_messages.append('Debe seleccionar una asignación')
        else:
            try:
                asignacion = Asignacion.objects.get(id=asignacion_id, estado=True)
            except Asignacion.DoesNotExist:
                error_messages.append('Asignación no válida o no disponible')

        if not tipo_pago or tipo_pago not in ['arena', 'divisas']:
            error_messages.append('Debe seleccionar un tipo de pago válido')

        if not confirmar:
            error_messages.append('Debe confirmar el pago')

        # Si no hay errores, procesar el pago
       # Redirigir a una página de éxito

    # Si es GET o hay errores, mostrar el formulario
    asignaciones_disponibles = Asignacion.objects.filter(estado=True)
    context = {
        'asignaciones': asignaciones_disponibles,
        'error_messages': error_messages,
        'valores_previos': {
            'asignacion_id': asignacion.id if asignacion else '',
            'tipo_pago': tipo_pago,
            'confirmar': confirmado
        }
    }
    return render(request, 'nomina/resultado_pago.html', context)