"""
Configuración de Django para el proyecto sistema.
"""

import os
from pathlib import Path

# --- Configuración Principal ---

# Directorio base del proyecto.
BASE_DIR = Path(__file__).resolve().parent.parent

# Clave secreta para la seguridad de la aplicación.
# ¡IMPORTANTE: Mantener en secreto en producción!
SECRET_KEY = 'django-insecure-)wgph*m*(kdpp+s$zz(bd4hy2g-1)xkrtiks-o4_o!)&*3#+2@'

# Clave para la encriptación Fernet para códigos QR.
FERNET_KEY = b'0k8nLk92yO-zLogb8MWaqyj2ihyl_m-dHYtlzgc7euU='

# Modo de depuración.
# ¡IMPORTANTE: Desactivar en producción!
DEBUG = True

# Hosts permitidos para la aplicación.
ALLOWED_HOSTS = []





# --- Definición de Aplicaciones y Middleware ---

# Aplicaciones instaladas en el proyecto.
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'arpeta', 
]

# Componentes de middleware utilizados.
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


# --- Plantillas ---

# Configuración del motor de plantillas.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')], # Directorio de plantillas global
        'APP_DIRS': True, # Buscar plantillas en directorios de aplicaciones
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


# --- Bases de Datos ---

# Configuración de la conexión a la base de datos.
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

# Validadores para la seguridad de las contraseñas.
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# --- Internacionalización ---

# Código de idioma.
LANGUAGE_CODE = 'es'

# Zona horaria.
TIME_ZONE = 'America/Caracas'

# Activar el sistema de traducción.
USE_I18N = True

# Usar información de zona horaria.
USE_TZ = True


# --- Archivos Estáticos y Multimedia ---

# URL para archivos estáticos.
# settings.py
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# Para producción, necesitarás esto para servir archivos estáticos en PDF
if DEBUG:
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
else:
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# --- Clave Primaria por Defecto ---

# Tipo de campo para claves primarias automáticas.
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --- Autenticación ---

# URL de inicio de sesión.
LOGIN_URL = '/login/'

# Backends de autenticación.
AUTHENTICATION_BACKENDS = [
    'arpeta.backends.EmailAuthBackend', # Autenticación por email
    'django.contrib.auth.backends.ModelBackend', # Autenticación por defecto de Django
]


# --- Configuración de Correo Electrónico ---

# Backend para envío de correos.
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# Servidor SMTP.
EMAIL_HOST = 'smtp.gmail.com'
# Puerto SMTP.
EMAIL_PORT = 587
# Usar TLS para la conexión.
EMAIL_USE_TLS = True
# Usuario SMTP.
EMAIL_HOST_USER = 'arpetasistema@gmail.com'
# Contraseña SMTP.
EMAIL_HOST_PASSWORD = 'sistema123'
# Remitente por defecto para correos del sistema.
DEFAULT_FROM_EMAIL = 'astryrosendo33@gmail.com'