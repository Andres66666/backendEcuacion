"""Django settings for main project."""

import os
from pathlib import Path
from datetime import timedelta
import cloudinary

# =====================================================
# Build paths inside the project like this: BASE_DIR / 'subdir'.
# =====================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# =====================================================
# SECURITY SETTINGS
# =====================================================
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "tu_clave_segura")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "backendecuacion.onrender.com").split(",")

# =====================================================
# Application definition
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
# Database
# =====================================================
import os

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "ecuacion"),
        "USER": os.environ.get("DB_USER", "ecuacion_user"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "aPNuMZDruvJcndzpKOwycaTecZYJMMu0"),
        "HOST": os.environ.get(
            "DB_HOST", "dpg-d38se1nfte5s73cc7j6g-a.oregon-postgres.render.com"
        ),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "OPTIONS": {
            "sslmode": "require",  # Esto es obligatorio para Render
        },
    }
}


# =====================================================
# Password validation
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
# Internationalization
# =====================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# =====================================================
# REST Framework & JWT
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
# Static and Media files
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
    cloud_name=os.getenv("CLOUD_NAME", "dexggkhkd"),
    api_key=os.getenv("CLOUDINARY_API_KEY", "896862494571978"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET", "-uWh6mQnL_5dUgI3LIE0rRYxVfI"),
    secure=True,
)

# =====================================================
# CORS & CSRF
# =====================================================
CORS_ALLOWED_ORIGINS = [
    "https://mallafinita.netlify.app",
    "http://mallafinita.netlify.app",
]

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()
CORS_ALLOW_CREDENTIALS = True
APPEND_SLASH = True

# =====================================================
# Security for production
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
# Miscellaneous
# =====================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# SQL Injection Defense trusted IPs and Domains
SQLI_DEFENSE_TRUSTED_IPS = [
    "127.0.0.1",
    "192.168.0.4",
    "192.168.0.7",
    "172.16.8.103",
    "172.16.10.11",
]

SQLI_DEFENSE_TRUSTED_DOMAINS = [
    "mallafinita.netlify.app",
]
