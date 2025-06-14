"""
Configuración de Django para el proyecto ARPETA.
"""

import os
from pathlib import Path

# --- Configuración Base ---
# --------------------------------------------------------------------------

# Directorio raíz del proyecto (donde se encuentra manage.py).
BASE_DIR = Path(__file__).resolve().parent.parent

# Directorio donde se guardarán los archivos subidos por los usuarios
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# URL base para servir los archivos multimedia
MEDIA_URL = '/media/'

# Ruta para las plantillas HTML globales del proyecto.
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')


# --- Seguridad y Modo de Ejecución ---
# --------------------------------------------------------------------------

# Clave secreta para seguridad (¡mantener en secreto en producción!).
SECRET_KEY = 'django-insecure-)wgph*m*(kdpp+s$zz(bd4hy2g-1)xkrtiks-o4_o!)&*3#+2@'

# Clave para encriptación Fernet (para códigos QR).
FERNET_KEY = b'0k8nLk92yO-zLogb8MWaqyj2ihyl_m-dHYtlzgc7euU='

# Modo de depuración (DEBUG). ¡Debe ser False en producción!
DEBUG = True

# Hosts permitidos para la aplicación (ej. 'tudominio.com').
# En desarrollo, generalmente incluye '127.0.0.1' y 'localhost'.
ALLOWED_HOSTS = []
if DEBUG:
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '::1']


# --- Aplicaciones y Middleware ---
# --------------------------------------------------------------------------

# Aplicaciones instaladas en el proyecto.
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Necesario para el dominio en los correos de recuperación.
    'arpeta',
]

# ID del sitio actual (usado por `django.contrib.sites`).
SITE_ID = 1

# Componentes de middleware que procesan las peticiones.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Archivo principal de URLs del proyecto.
ROOT_URLCONF = 'sistema.urls'

# Aplicación WSGI para el servidor.
WSGI_APPLICATION = 'sistema.wsgi.application'


# --- Configuración de Plantillas ---
# --------------------------------------------------------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],  # Directorio de plantillas global.
        'APP_DIRS': True,        # Busca plantillas dentro de cada aplicación.
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# --- Base de Datos ---
# --------------------------------------------------------------------------

# Configuración de la conexión a la base de datos PostgreSQL.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'arpeta_4',
        'USER': 'postgres',
        'PASSWORD': 'mia2712',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


# --- Validación de Contraseñas ---
# --------------------------------------------------------------------------

# Validadores para la seguridad de las contraseñas de usuario.
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- Internacionalización ---
# --------------------------------------------------------------------------

LANGUAGE_CODE = 'es'          # Idioma de la aplicación.
TIME_ZONE = 'America/Caracas' # Zona horaria (Venezuela).
USE_I18N = True               # Activa el sistema de traducción.
USE_TZ = True                 # Usa información de zona horaria en datetimes.


# --- Archivos Estáticos ---
# --------------------------------------------------------------------------

# URL para servir archivos estáticos (CSS, JS, imágenes).
STATIC_URL = 'static/'

# Si usas STATIC_ROOT para producción (es para collectstatic)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Si tienes archivos estáticos a nivel de proyecto o en otras ubicaciones
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'), # Asegúrate de que esta línea exista si pusiste Font Awesome aquí
]

# Tipo de campo para claves primarias automáticas (BigAutoField para mayor rango).
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- Autenticación ---
# --------------------------------------------------------------------------

# URL de redirección para inicio de sesión requerido.
LOGIN_URL = '/login/'

# Backends de autenticación para verificar usuarios.
AUTHENTICATION_BACKENDS = [
    'arpeta.backends.EmailAuthBackend',  # Autenticación personalizada por email.
    'django.contrib.auth.backends.ModelBackend', # Autenticación por defecto de Django.
]


# --- Configuración de Correo Electrónico ---
# --------------------------------------------------------------------------

# Backend para el envío de correos (SMTP para correos reales).
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'       # Servidor SMTP (ej. Gmail).
EMAIL_PORT = 587                    # Puerto SMTP (587 para TLS).
EMAIL_USE_TLS = True                # Usar TLS para conexión segura.
EMAIL_HOST_USER = 'manzola416@gmail.com' # Tu dirección de correo.
# Contraseña de la cuenta de correo. ¡Usa una contraseña de aplicación para Gmail!
EMAIL_HOST_PASSWORD = 'nxhf aiwo lhyn zytq'
DEFAULT_FROM_EMAIL = 'manzola416@gmail.com' # Remitente por defecto.