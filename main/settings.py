"""Django settings for main project (backendecuacion)."""

from pathlib import Path
from datetime import timedelta
import os
from decouple import config
import cloudinary

# =====================================================
# === 1. RUTAS BASE Y CLAVES DE SEGURIDAD ============
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Se carga desde el entorno de Render (o usa valor por defecto solo para DEV)
SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-(fn$sd-g@*)51f7)nc!a^3xeb(ma^9f6pm02_a+2h6tw^251fq",
)
# Se carga desde el entorno de Render, y se convierte a booleano. ¡Clave para Prod!
DEBUG = config("DEBUG", default=False, cast=bool)

# Usamos ALLOWED_HOSTS dinámico según el modo DEBUG (como en tu ejemplo funcional)
if DEBUG:
    ALLOWED_HOSTS = ["*"]  # Permite todo en desarrollo local
else:
    # Solo el dominio de Render para producción
    ALLOWED_HOSTS = [
        "backendecuacion.onrender.com",
    ]

# Añadimos hosts locales si no estamos en producción forzada
if "127.0.0.1" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.extend(["127.0.0.1", "localhost"])

# Nota: Eliminé la IP "192.168.0.4" ya que no es necesaria en un despliegue cloud.

APPEND_SLASH = True

# =====================================================
# === 2. APLICACIONES INSTALADAS ======================
# =====================================================

INSTALLED_APPS = [
    # Django apps básicas
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Librerías externas
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    # Módulos 2FA
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "two_factor",
    # Almacenamiento
    "cloudinary_storage",  # <--- AÑADIDO: Módulo para Cloudinary Storage
    # Aplicaciones locales
    "users",
]

# =====================================================
# === 3. MIDDLEWARES ==================================
# =====================================================

MIDDLEWARE = [
    # Whitenoise debe ir justo después de SecurityMiddleware
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # <--- AÑADIDO: Necesario para servir estáticos en Render
    # Seguridad y CORS
    "corsheaders.middleware.CorsMiddleware",
    # Sesión y requests
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    # Autenticación
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    # Mensajes y UI
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =====================================================
# === 4. URLS, TEMPLATES Y APLICACIÓN WSGI ============
# =====================================================

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
# === 5. BASE DE DATOS ================================
# =====================================================

# El uso de os.getenv con valores por defecto está bien,
# pero asegúrate de que estas variables de entorno están en Render.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "ecuacion_wtpx"),
        "USER": os.getenv("DB_USER", "ecuacion_wtpx_user"),
        "PASSWORD": os.getenv("DB_PASSWORD", "hHSiKOLZtIxbxmvw3W9MWADpB2x7xBjR"),
        "HOST": os.getenv(
            "DB_HOST", "dpg-d3i6ttre5dus738shkig-a.oregon-postgres.render.com"
        ),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}
# =====================================================
# === 6. CONFIGURACIÓN DE AUTH Y PASSWORDS ============
# =====================================================

LOGIN_URL = "two_factor:login"
LOGIN_REDIRECT_URL = "two_factor:profile"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =====================================================
# === 7. CONFIGURACIÓN DE DRF Y JWT ===================
# =====================================================

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Solo si usas DRF Spectacular
    # "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
}

# =====================================================
# === 8. INTERNACIONALIZACIÓN =========================
# =====================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# =====================================================
# === 9. CONFIGURACIÓN DE EMAIL =======================
# =====================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# Se recomienda usar os.getenv/config para las credenciales
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="benitoandrescalle035@gmail.com")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="hmczrcgooenggoms")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# =====================================================
# === 10. ARCHIVOS ESTÁTICOS Y MULTIMEDIA ============
# =====================================================

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
# Asegúrate de usar Whitenoise de la forma correcta
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"

DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUD_NAME", "dexggkhkd"),
    "API_KEY": os.getenv("CLOUDINARY_API_KEY", "896862494571978"),
    "API_SECRET": os.getenv("CLOUDINARY_API_SECRET", "-uWh6mQnL_5dUgI3LIE0rRYxVfI"),
    "SECURE": True,
}

# La llamada a cloudinary.config ya no es estrictamente necesaria si usas CLOUDINARY_STORAGE
# Pero si la mantienes, asegúrate de que usa la variable 'secure' en True.
cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE["CLOUD_NAME"],
    api_key=CLOUDINARY_STORAGE["API_KEY"],
    api_secret=CLOUDINARY_STORAGE["API_SECRET"],
    secure=True,
)

# =====================================================
# === 11. CORS Y CSRF ================================
# =====================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "https://mallafinita.netlify.app",
]

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()
CORS_ALLOW_CREDENTIALS = True

# =====================================================
# === 12. SEGURIDAD EN PRODUCCIÓN =====================
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
# === 14. AUTO FIELD Y CONFIGURACIÓN FINAL ============
# =====================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
