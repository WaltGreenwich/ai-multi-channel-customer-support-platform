"""
Configuración Django para Fran Bot
"""
import os
from pathlib import Path
from decouple import config, Csv

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# ═══════════════════════════════════════════════════════
# SEGURIDAD
# ═══════════════════════════════════════════════════════
SECRET_KEY = config(
    'SECRET_KEY', default='django-insecure-dev-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,0.0.0.0,.ngrok-free.dev,.ngrok.io',
    cast=Csv(),
)

# ═══════════════════════════════════════════════════════
# APLICACIONES
# ═══════════════════════════════════════════════════════
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',  # Para campos avanzados PostgreSQL

    # Apps del proyecto
    'apps.bot',
    'apps.integrations',
    'apps.api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
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

WSGI_APPLICATION = 'config.wsgi.application'

# ═══════════════════════════════════════════════════════
# BASE DE DATOS
# ═══════════════════════════════════════════════════════
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='fran_bot_db'),
        'USER': config('DB_USER', default='fran_user'),
        'PASSWORD': config('DB_PASSWORD', default='fran_password'),
        'HOST': config('DB_HOST', default='db'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# ═══════════════════════════════════════════════════════
# CELERY
# ═══════════════════════════════════════════════════════
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = config(
    'CELERY_RESULT_BACKEND', default='redis://redis:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'America/Lima'

# ═══════════════════════════════════════════════════════
# INTERNACIONALIZACIÓN
# ═══════════════════════════════════════════════════════
LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

# ═══════════════════════════════════════════════════════
# ARCHIVOS ESTÁTICOS Y MULTIMEDIA
# ═══════════════════════════════════════════════════════
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ═══════════════════════════════════════════════════════
# GOOGLE GEMINI
# ═══════════════════════════════════════════════════════
GOOGLE_API_KEY = config('GOOGLE_API_KEY', default='')

# ═══════════════════════════════════════════════════════
# TELEGRAM
# ═══════════════════════════════════════════════════════
USE_TELEGRAM = config('USE_TELEGRAM', default=False, cast=bool)
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default='')
BASE_URL = config('BASE_URL', default='http://localhost:8000')

# ═══════════════════════════════════════════════════════
# WHATSAPP
# ═══════════════════════════════════════════════════════
USE_WHATSAPP = config('USE_WHATSAPP', default=False, cast=bool)
WHATSAPP_PHONE_ID = config('WHATSAPP_PHONE_ID', default='')
WHATSAPP_TOKEN = config('WHATSAPP_TOKEN', default='')
WHATSAPP_VERIFY_TOKEN = config(
    'WHATSAPP_VERIFY_TOKEN', default='fran_bot_webhook_secret_2025')

# ═══════════════════════════════════════════════════════
# GMAIL
# ═══════════════════════════════════════════════════════
USE_GMAIL = config('USE_GMAIL', default=False, cast=bool)
GMAIL_CLIENT_ID = config('GMAIL_CLIENT_ID', default='')
GMAIL_CLIENT_SECRET = config('GMAIL_CLIENT_SECRET', default='')
GMAIL_REFRESH_TOKEN = config('GMAIL_REFRESH_TOKEN', default='')

# ═══════════════════════════════════════════════════════
# TRELLO
# ═══════════════════════════════════════════════════════
TRELLO_API_KEY = config('TRELLO_API_KEY', default='')
TRELLO_TOKEN = config('TRELLO_TOKEN', default='')
TRELLO_BOARD_ID = config('TRELLO_BOARD_ID', default='')
TRELLO_LIST_ID = config('TRELLO_LIST_ID', default='')

# ═══════════════════════════════════════════════════════
# SUPABASE
# ═══════════════════════════════════════════════════════
USE_SUPABASE = config('USE_SUPABASE', default=False, cast=bool)
SUPABASE_URL = config('SUPABASE_URL', default='')
SUPABASE_KEY = config('SUPABASE_KEY', default='')
SUPABASE_BUCKET = config('SUPABASE_BUCKET', default='fran-bot-media')

# ═══════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# ═══════════════════════════════════════════════════════
# OTROS
# ═══════════════════════════════════════════════════════
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CSRF
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]
