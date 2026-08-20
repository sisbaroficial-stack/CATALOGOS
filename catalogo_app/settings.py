from pathlib import Path
import os

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - opcional para desarrollo local
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent.parent
if load_dotenv:
    load_dotenv(BASE_DIR / '.env')

def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {'1', 'true', 'yes', 'on'}


DEBUG = env_bool('DJANGO_DEBUG', True)
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'django-insecure-local-development-only'
    else:
        raise ImproperlyConfigured('DJANGO_SECRET_KEY debe configurarse en producción.')

ALLOWED_HOSTS = [host.strip() for host in os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost,testserver').split(',') if host.strip()]
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if origin.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'catalogo',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'catalogo_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'catalogo.context_processors.catalogo_config',
            ],
        },
    },
]

WSGI_APPLICATION = 'catalogo_app.wsgi.application'
ASGI_APPLICATION = 'catalogo_app.asgi.application'

DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = Path(os.getenv('MEDIA_ROOT', BASE_DIR / 'media'))
SERVE_MEDIA = env_bool('SERVE_MEDIA', DEBUG)

# En producción, Render no conserva archivos escritos en su disco local. Al
# establecer MEDIA_STORAGE=r2, todos los ImageField/FileField existentes
# guardan y leen los archivos directamente desde Cloudflare R2 (S3-compatible).
MEDIA_STORAGE = os.getenv('MEDIA_STORAGE', 'filesystem').strip().lower()

if MEDIA_STORAGE not in {'filesystem', 'r2'}:
    raise ImproperlyConfigured('MEDIA_STORAGE debe ser "filesystem" o "r2".')

if MEDIA_STORAGE == 'r2':
    R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID', '').strip()
    R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID', '').strip()
    R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY', '').strip()
    R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME', '').strip()
    R2_PUBLIC_DOMAIN = os.getenv('R2_PUBLIC_DOMAIN', '').strip()
    missing_r2_settings = [
        name for name, value in {
            'R2_ACCOUNT_ID': R2_ACCOUNT_ID,
            'R2_ACCESS_KEY_ID': R2_ACCESS_KEY_ID,
            'R2_SECRET_ACCESS_KEY': R2_SECRET_ACCESS_KEY,
            'R2_BUCKET_NAME': R2_BUCKET_NAME,
            'R2_PUBLIC_DOMAIN': R2_PUBLIC_DOMAIN,
        }.items() if not value
    ]
    if missing_r2_settings:
        raise ImproperlyConfigured(
            'Faltan variables de Cloudflare R2: ' + ', '.join(missing_r2_settings)
        )

    # django-storages espera únicamente el host, sin protocolo ni barra final.
    R2_PUBLIC_DOMAIN = R2_PUBLIC_DOMAIN.removeprefix('https://').removeprefix('http://').rstrip('/')
    default_storage = {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'access_key': R2_ACCESS_KEY_ID,
            'secret_key': R2_SECRET_ACCESS_KEY,
            'bucket_name': R2_BUCKET_NAME,
            'region_name': os.getenv('R2_REGION', 'auto'),
            'endpoint_url': f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
            'custom_domain': R2_PUBLIC_DOMAIN,
            'querystring_auth': False,
            'file_overwrite': True,
        },
    }
else:
    default_storage = {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    }

STORAGES = {
    'default': default_storage,
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', not DEBUG)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/panel/login/'
LOGIN_REDIRECT_URL = '/panel/'
LOGOUT_REDIRECT_URL = '/panel/login/'

MESSAGE_TAGS = {
    10: 'debug',
    20: 'info',
    25: 'success',
    30: 'warning',
    40: 'danger',
}
