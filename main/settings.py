"""
Django settings for main project.  (Versión segura y lista para Render)
Use variables de entorno para credenciales sensibles.
"""

from pathlib import Path
from datetime import timedelta
import os
import json
import cloudinary

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# === Seguridad / Entorno ===
# En producción: define SECRET_KEY en las Environment Variables de Render
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "cambia-esto-en-local-usa-env")

# DEBUG debe ser False en producción
DEBUG = os.getenv("DEBUG", "0") in ("1", "true", "True")

# Hosts permitidos (añade aquí dominios custom)
ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS", "backendecuacion.onrender.com,localhost,127.0.0.1"
).split(",")

# === Aplicaciones instaladas ===
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",  # debe ir arriba en MIDDLEWARE
    "rest_framework",
    "rest_framework_simplejwt",
    "users",
]

# === REST Framework / Simple JWT ===
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(os.getenv("JWT_ACCESS_MINUTES", 60))
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", 1))),
    "ROTATE_REFRESH_TOKENS": True,
}

# === Middleware ===
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # debe ser la primera relacionada a CORS
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Middlewares personalizados (descomentar si están probados)
    # "GuardianUnivalle_Benito_Yucra.detectores.detector_sql.SQLIDefenseMiddleware",
    # "users.middleware.AuditoriaMiddleware",
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

# === Base de datos (usar variables de entorno en Render) ===
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "ecuacion"),
        "USER": os.getenv("DB_USER", "ecuacion_user"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv(
            "DB_HOST", "dpg-d38se1nfte5s73cc7j6g-a.oregon-postgres.render.com"
        ),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# === Password validators ===
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# === Internacionalización ===
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# === Archivos estáticos y multimedia ===
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = os.getenv(
    "STATICFILES_STORAGE", "whitenoise.storage.CompressedManifestStaticFilesStorage"
)

MEDIA_URL = "/media/"

# Cloudinary: leer credenciales desde ENV
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUD_NAME", ""),
    "API_KEY": os.getenv("CLOUDINARY_API_KEY", ""),
    "API_SECRET": os.getenv("CLOUDINARY_API_SECRET", ""),
    "SECURE": True,
}
DEFAULT_FILE_STORAGE = os.getenv(
    "DEFAULT_FILE_STORAGE", "cloudinary_storage.storage.MediaCloudinaryStorage"
)

# Inicializar cloudinary (seguro)
if CLOUDINARY_STORAGE["API_KEY"] and CLOUDINARY_STORAGE["API_SECRET"]:
    cloudinary.config(
        cloud_name=CLOUDINARY_STORAGE["CLOUD_NAME"],
        api_key=CLOUDINARY_STORAGE["API_KEY"],
        api_secret=CLOUDINARY_STORAGE["API_SECRET"],
        secure=True,
    )

# === CORS / CSRF ===
# Define los orígenes frontend permitidos (Netlify y dev). En Render configura estas ENV si cambian.
CORS_ALLOWED_ORIGINS = json.loads(
    os.getenv("CORS_ALLOWED_ORIGINS_JSON", '["https://mallafinita.netlify.app"]')
)
CSRF_TRUSTED_ORIGINS = json.loads(
    os.getenv("CSRF_TRUSTED_ORIGINS_JSON", '["https://mallafinita.netlify.app"]')
)

CORS_ALLOW_CREDENTIALS = True
APPEND_SLASH = True

# === Seguridad (activar en producción) ===
if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "1") in ("1", "true", "True")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", 31536000))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# === Trusted IPs / dominios para tu detector SQL (opcional) ===
SQLI_DEFENSE_TRUSTED_IPS = os.getenv("SQLI_DEFENSE_TRUSTED_IPS", "127.0.0.1").split(",")
SQLI_DEFENSE_TRUSTED_DOMAINS = json.loads(
    os.getenv("SQLI_DEFENSE_TRUSTED_DOMAINS_JSON", '["mallafinita.netlify.app"]')
)

# === Logging (útil en Render para ver tracebacks) ===
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG" if DEBUG else "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
    },
}

# === Opcionales / recomendaciones adicionales ===
# - Asegúrate de definir en Render las ENV: DJANGO_SECRET_KEY, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT,
#   CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET,
#   CORS_ALLOWED_ORIGINS_JSON, CSRF_TRUSTED_ORIGINS_JSON, SQLI_DEFENSE_TRUSTED_DOMAINS_JSON
#
# - Para CORS JSON example: '["https://mallafinita.netlify.app","http://localhost:4200"]'
#
# - No dejes DEBUG=True en producción (pásalo a '0' en la ENV)
#
# - Si usas middlewares personalizados, coméntalos mientras depuras y activa cuando estén testeados.
#
# - Para desplegar: borra migraciones locales mal formadas, ejecuta migrate en Render (o en deploy hooks).
#
# - Revisa que SIMPLE_JWT y la implementación de tu modelo Usuario sean compatibles (i.e., is_active, get_username, etc.)
