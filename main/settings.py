"""Django settings for main project."""

from pathlib import Path
from datetime import timedelta
import os
from decouple import config
import cloudinary

# ========================================
# BASE CONFIGURATION
# ========================================
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-(fn$sd-g@*)51f7)nc!a^3xeb(ma^9f6pm02_a+2h6tw^251fq"
DEBUG = (
    os.getenv("DEBUG", "True").lower() == "true"
)  # False en Render por variable de entorno

# ========================================
# HOSTS
# ========================================
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") + [
    "backendecuacion.onrender.com"
]

# ========================================
# APPS
# ========================================
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
    # 2FA / OTP
    "django_otp",
    "django_otp.plugins.otp_static",
    "django_otp.plugins.otp_totp",
    "two_factor",
]

# ========================================
# REST FRAMEWORK
# ========================================
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# ========================================
# MIDDLEWARE
# ========================================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # ← Debe ir antes de CommonMiddleware
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Tus middlewares personalizados al final
    "GuardianUnivalle_Benito_Yucra.detectores.detector_sql.SQLIDefenseMiddleware",
    "GuardianUnivalle_Benito_Yucra.detectores.detector_xss.XSSDefenseMiddleware",
    "users.middleware.AuditoriaMiddleware",
]

# ========================================
# URLS / WSGI
# ========================================
ROOT_URLCONF = "main.urls"
WSGI_APPLICATION = "main.wsgi.application"

# ========================================
# DATABASE (Render o local)
# ========================================
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

# ========================================
# AUTH & JWT
# ========================================
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ========================================
# EMAIL
# ========================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "benitoandrescalle035@gmail.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "hmczrcgooenggoms")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

LOGIN_URL = "two_factor:login"
LOGIN_REDIRECT_URL = "two_factor:profile"

# ========================================
# INTERNATIONALIZATION
# ========================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ========================================
# STATIC / MEDIA / CLOUDINARY
# ========================================
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

# ========================================
# CORS & CSRF
# ========================================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "https://mallafinita.netlify.app",
]

CSRF_TRUSTED_ORIGINS = [
    "https://mallafinita.netlify.app",
    "https://backendecuacion.onrender.com",
]

# Durante pruebas
CORS_ALLOW_ALL_ORIGINS = True  # ⚠️ Desactiva en producción
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = ["*"]

APPEND_SLASH = True

# ========================================
# SECURITY (solo en producción)
# ========================================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ========================================
# DEFAULTS
# ========================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
