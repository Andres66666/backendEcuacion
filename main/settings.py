from pathlib import Path
from datetime import timedelta
import os

from decouple import config
import cloudinary
from argon2.low_level import Type as Argon2Type

# ====================================================
# === 1. RUTAS BASE Y CLAVES DE SEGURIDAD ============ 74707215
# ====================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-(fn$sd-g@*)51f7)nc!a^3xeb(ma^9f6pm02_a+2h6tw^251fq"
DEBUG = True

ALLOWED_HOSTS = [
    "192.168.1.15",
    "127.0.0.1",
    "localhost",
    "mallafinita.netlify.app",
    "backendecuacion.onrender.com",
    "pseudocourteous-jasperated-shavonne.ngrok-free.dev",
]

APPEND_SLASH = True

# =====================================================
# === 2. APLICACIONES INSTALADAS ======================
# =====================================================

INSTALLED_APPS = [
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
    "django_otp.plugins.otp_static",  # Códigos de respaldo
    "django_otp.plugins.otp_totp",  # Autenticador TOTP
    "two_factor",
    # Aplicaciones locales
    "users",
]

# =====================================================
# === 3. MIDDLEWARES ==================================
# =====================================================

MIDDLEWARE = [
    # Seguridad y CORS
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
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

    # --- Middlewares GuardianUnivalle ---
    #"GuardianUnivalle_Benito_Yucra.detectores.detector_sql.SQLIDefenseCryptoMiddleware",
    #"GuardianUnivalle_Benito_Yucra.detectores.detector_xss.XSSDefenseCryptoMiddleware",
    #"GuardianUnivalle_Benito_Yucra.detectores.detector_csrf.CSRFDefenseMiddleware",    
    #"GuardianUnivalle_Benito_Yucra.detectores.detector_dos.DOSDefenseMiddleware",
    
    # Auditoría app
    #"users.middleware.AuditoriaMiddleware",
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "ecuacion_1y5h",
        "USER": "ecuacion_1y5h_user",
        "PASSWORD": "5vWAIqGp4T2k8An4eR9Bk6ffzHEFmfkM",
        "HOST": "dpg-d6bnv795pdvs73erthr0-a.oregon-postgres.render.com",
        "PORT": "5432",
    }
} 

""" DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "Ecuacion",
        "USER": "postgres",
        "PASSWORD": "13247291",
        "HOST": "localhost",
        "PORT": "5432",
    }
} """
# =====================================================
# === 6. CONFIGURACIÓN DE AUTH Y PASSWORDS ============
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
# === 7. CONFIGURACIÓN DE DRF Y JWT ===================
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
# === 8. INTERNACIONALIZACIÓN =========================
# =====================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# =====================================================
# === 9. CONFIGURACIÓN DE EMAIL ======================= Contraseñas de aplicaciones
# =====================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "benitoandrescalle035@gmail.com"
EMAIL_HOST_PASSWORD = "frolnsnpgizgmtqh"


DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# =====================================================
# === 10. ARCHIVOS ESTÁTICOS Y MULTIMEDIA ============
# =====================================================

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUD_NAME", "dsbgmboh1"),
    "API_KEY": os.getenv("CLOUDINARY_API_KEY", "167689378512456"),
    "API_SECRET": os.getenv("CLOUDINARY_API_SECRET", "T4c-GP9KSbMKC74aGMnBCO1mjpY"),
    "SECURE": True,
}

cloudinary.config(
    cloud_name="dsbgmboh1",
    api_key="167689378512456",
    api_secret="T4c-GP9KSbMKC74aGMnBCO1mjpY",
    secure=True,
)

# =====================================================
# === 11. CORS Y CSRF ================================
# =====================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "https://mallafinita.netlify.app",
    "https://backendecuacion.onrender.com",
    "https://pseudocourteous-jasperated-shavonne.ngrok-free.dev",
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
# === 13. DEFENSAS (SQLi, XSS, CSRF, DoS) =============
# =====================================================

# -----------------------
# DoS Defense (Score)
# -----------------------
DOS_LIMITE_PETICIONES = 120
DOS_VENTANA_SEGUNDOS = 60
DOS_TIEMPO_BLOQUEO = 300

DOS_PESO = 0.6              
DOS_LIMITE_ENDPOINTS = 80       


DOS_PESO_BLACKLIST = 0.15      
DOS_PESO_HEURISTICA = 0.25     
DOS_UMBRAL_BLOQUEO = 0.8       

DOS_WARN_RATIO = 0.75
DOS_WARN_MIN_SCORE = 0.20
DOS_WARN_MIN_REQ = 10
DOS_TRUSTED_IPS = ["127.0.0.1", "192.168.1.15"]

DOS_WARN_RATE_RATIO = 0.75      
DOS_WARN_MIN_SCORE = 0.12      

DOS_BLACKLIST_CACHE_KEY = "dos:blacklist:set"
DOS_BLACKLIST_REFRESH_SECONDS = 60 * 60 * 6  

DOS_DEFENSE_HASH = "SHA256"     

# -----------------------
# SQL Injection Defense
# -----------------------
SQLI_DEFENSE_TRUSTED_IPS = ["127.0.0.1", "192.168.1.15"]

# -----------------------
# XSS Defense
# -----------------------
XSS_DEFENSE_TRUSTED_IPS = ["127.0.0.1", "192.168.1.15"]
XSS_DEFENSE_SANITIZE_INPUT = False
XSS_DEFENSE_BLOCK = True
XSS_DEFENSE_EXCLUDED_PATHS = ["/health", "/internal"]

# -----------------------
# CSRF Defense
# -----------------------
CSRF_DEFENSE_TRUSTED_IPS = ["127.0.0.1", "192.168.1.15"]
CSRF_DEFENSE_BLOCK = True
CSRF_DEFENSE_LOG = True

# =====================================================
# === 14. AUTO FIELD Y CONFIGURACIÓN FINAL ============
# =====================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Claves maestras (base64 32 bytes)
CSRF_DEFENSE_MASTER_KEY = "t9G6OYbT9ldFf/XSKmdsiAQMUmJiD8atbxtRI+SzK/s="
SQLI_DEFENSE_MASTER_KEY = "t9G6OYbT9ldFf/XSKmdsiAQMUmJiD8atbxtRI+SzK/s="
XSS_DEFENSE_MASTER_KEY = "t9G6OYbT9ldFf/XSKmdsiAQMUmJiD8atbxtRI+SzK/s="

# Opciones criptográficas CSRF
CSRF_DEFENSE_AEAD = "AESGCM"  # o "CHACHA20"
CSRF_DEFENSE_ARGON2 = {
    "time_cost": 2,
    "memory_cost": 65536,
    "parallelism": 1,
    "hash_len": 32,
    "type": Argon2Type.ID,
}
CSRF_DEFENSE_HASH = "SHA256"  # o "SHA3"

CSRF_HMAC_LABEL = b"csrfdefense-hmac"
CSRF_AEAD_LABEL = b"csrfdefense-aead"

CSRF_DEFENSE_MIN_SIGNALS = 1
CSRF_DEFENSE_EXCLUDED_API_PREFIXES = []

CSRF_DEFENSE_EXCLUDED_PATHS = []
CSRF_DEFENSE_WEIGHT = 0.2
CSRF_DEFENSE_BLOCK_REQUIRE_ORIGIN_MISMATCH = True
CSRF_DEFENSE_BLOCK_SCORE = 0.35

# Frontend
FRONTEND_URL = "http://localhost:4200"

# Cache prefix
CACHE_MIDDLEWARE_KEY_PREFIX = "mallafinita"

# Redis cache
""" CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv(
            "REDIS_URL",
            "redis://default:wE7lakzG2ngqg8pa6VAHbBG5WLl5EYSA@redis-13312.c253.us-central1-1.gce.cloud.redislabs.com:13312/0",
        ),
        "OPTIONS": {
            "PASSWORD": os.getenv("REDIS_PASSWORD", None),
        },
    }
} """