"""Django settings for main project."""

from pathlib import Path
from datetime import timedelta
import os
import cloudinary
from corsheaders.defaults import default_headers

# =====================================================
# BASE
# =====================================================
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-(fn$sd-g@*)51f7)nc!a^3xeb(ma^9f6pm02_a+2h6tw^251fq",
)

DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    "backendecuacion.onrender.com",
    "localhost",
    "127.0.0.1",
]

# =====================================================
# APPLICATIONS
# =====================================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "users",
]

# =====================================================
# MIDDLEWARE
# =====================================================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "GuardianUnivalle_Benito_Yucra.detectores.detector_sql.SQLIDefenseMiddleware",
    "users.middleware.AuditoriaMiddleware",
]

ROOT_URLCONF = "main.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "main.wsgi.application"

# =====================================================
# DATABASE
# =====================================================
""" DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "ecuacion"),
        "USER": os.getenv("DB_USER", "ecuacion_user"),
        "PASSWORD": os.getenv("DB_PASSWORD", "aPNuMZDruvJcndzpKOwycaTecZYJMMu0"),
        "HOST": os.getenv(
            "DB_HOST", "dpg-d38se1nfte5s73cc7j6g-a.oregon-postgres.render.com"
        ),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
} """
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "ecuacion"),
        "USER": os.getenv("DB_USER", "ecuacion_user"),
        "PASSWORD": os.getenv("DB_PASSWORD", "aPNuMZDruvJcndzpKOwycaTecZYJMMu0"),
        "HOST": os.getenv(
            "DB_HOST", "dpg-d38se1nfte5s73cc7j6g-a.oregon-postgres.render.com"
        ),
        "PORT": os.getenv("DB_PORT", "5432"),
        "OPTIONS": {  # ← Agrega esto
            "sslmode": "require",  # Obliga SSL; Render lo maneja
        },
        # Opcional: Si usas psycopg3, agrega "OPTIONS": {"channel_binding": "disable"} si hay issues con channel binding.
    }
}


# =====================================================
# PASSWORD VALIDATION
# =====================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =====================================================
# INTERNATIONALIZATION
# =====================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# =====================================================
# REST FRAMEWORK
# =====================================================
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
}

# =====================================================
# CORS & CSRF
# =====================================================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "https://mallafinita.netlify.app",
]

CSRF_TRUSTED_ORIGINS = [
    "https://mallafinita.netlify.app",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = list(default_headers) + [
    "content-type",
    "authorization",
    "x-requested-with",
]

# =====================================================
# SQLI DEFENSE MIDDLEWARE
# =====================================================
SQLI_DEFENSE_TRUSTED_ORIGINS = [
    "https://mallafinita.netlify.app",
]

SQLI_DEFENSE_TRUSTED_IPS = [
    "127.0.0.1",
    "192.168.0.4",
]

SQLI_DEFENSE_EXEMPT_PATHS = [
    "/api/login/",
    "/api/token/",
    "/api/rol/",
    "/api/permiso/",
    "/api/usuario/",
    "/api/usuario_rol/",
    "/api/rol_permiso/",
    "/api/IdGeneral/",
    "/api/GastosOperaciones/",
    "/api/modulos/",
    "/api/materiales/",
    "/api/mano_de_obra/",
    "/api/equipo_herramienta/",
    "/api/gastos_generales/",
    "/api/auditoria_db/",
]

# =====================================================
# STATIC & MEDIA
# =====================================================
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUD_NAME", "dexggkhkd"),
    "API_KEY": os.getenv("CLOUDINARY_API_KEY", "896862494571978"),
    "API_SECRET": os.getenv("CLOUDINARY_API_SECRET", "-uWh6mQnL_5dUgI3LIE0rRYxVfI"),
    "SECURE": True,
}

cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE["CLOUD_NAME"],
    api_key=CLOUDINARY_STORAGE["API_KEY"],
    api_secret=CLOUDINARY_STORAGE["API_SECRET"],
    secure=True,
)

# =====================================================
# SEGURIDAD SSL PRODUCCIÓN
# =====================================================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# =====================================================
# CONFIG ADICIONAL
# =====================================================
APPEND_SLASH = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
