"""Django settings for main project (backendecuacion)."""

from pathlib import Path
from datetime import timedelta
import os
from decouple import config
import cloudinary

# =====================================================
# 1. RUTAS BASE Y CLAVES DE SEGURIDAD
# =====================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# Clave secreta (debe estar en entorno para producción)
SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-(fn$sd-g@*)51f7)nc!a^3xeb(ma^9f6pm02_a+2h6tw^251fq"
)

# =====================================================
# 2. ENTORNO Y DEBUG AUTOMÁTICO
# =====================================================
ENVIRONMENT = config("ENVIRONMENT", default="development")  # 'development' o 'production'
DEBUG = ENVIRONMENT == "development"

# =====================================================
# 3. HOSTS Y CORS SEGÚN ENTORNO
# =====================================================
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "192.168.0.4",
    "backendecuacion.onrender.com",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "https://mallafinita.netlify.app",
]

# También permite orígenes adicionales en caso de subdominios o redirecciones
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.netlify\.app$",
]

CSRF_TRUSTED_ORIGINS = [
    "https://mallafinita.netlify.app",
    "https://backendecuacion.onrender.com",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_HEADERS = True
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

# =====================================================
# 4. APLICACIONES INSTALADAS
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
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "two_factor",

    # Aplicaciones locales
    "users",
]

# =====================================================
# 5. MIDDLEWARES
# =====================================================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "GuardianUnivalle_Benito_Yucra.detectores.detector_dos.DOSDefenseMiddleware", # esto esta bien 
    "GuardianUnivalle_Benito_Yucra.detectores.detector_sql.SQLIDefenseMiddleware", #  problema  SQLIDefenseMiddleware cambios
    # esto se agrego
    "users.middleware.AuditoriaMiddleware",
]

# =====================================================
# 6. URLS, TEMPLATES Y WSGI
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
# 7. BASE DE DATOS
# =====================================================
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
# 8. CONFIGURACIÓN DE AUTENTICACIÓN Y CONTRASEÑAS
# =====================================================
LOGIN_URL = "two_factor:login"
LOGIN_REDIRECT_URL = "two_factor:profile"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =====================================================
# 9. CONFIGURACIÓN DE DRF Y JWT
# =====================================================
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
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
}

# =====================================================
# 10. INTERNACIONALIZACIÓN
# =====================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# =====================================================
# 11. CONFIGURACIÓN DE EMAIL
# =====================================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "benitoandrescalle035@gmail.com"
EMAIL_HOST_PASSWORD = "hmczrcgooenggoms"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# =====================================================
# 12. ARCHIVOS ESTÁTICOS Y MULTIMEDIA
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
    cloud_name="dexggkhkd",
    api_key="896862494571978",
    api_secret="-uWh6mQnL_5dUgI3LIE0rRYxVfI",
    secure=True,
)

# =====================================================
# 13. SEGURIDAD EN PRODUCCIÓN
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
# === 14. DEFENSAS (SQLi y XSS) =======================
# =====================================================

# --- DoS Defense ---
DOS_DEFENSE_MAX_REQUESTS = 100  # máximo requests por minuto
DOS_DEFENSE_BLOCK_TIME = 300  # segundos para bloquear IP sospechosa
DOS_DEFENSE_TRUSTED_IPS = [
    "https://mallafinita.netlify.app",
    "https://backendecuacion.onrender.com",
    "127.0.0.1",
    "192.168.0.4",
]
# --- SQL Injection Defense ---
# IPs confiables
SQLI_DEFENSE_TRUSTED_IPS = [
    "127.0.0.1",
    "192.168.0.4",
    "localhost",
]

# URLs confiables (pueden ser backend y frontend)
SQLI_DEFENSE_TRUSTED_URLS = [
    "https://backendecuacion.onrender.com",
    "https://mallafinita.netlify.app",
]
# =====================================================
# 15. AUTO FIELD Y LOGS
# =====================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Mostrar entorno actual (útil para depurar)
print(f"🔧 Entorno activo: {ENVIRONMENT} | DEBUG={DEBUG}")
