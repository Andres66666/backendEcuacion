"""Django settings for main project."""

from pathlib import Path
from datetime import timedelta
import os
from decouple import config
import cloudinary

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-(fn$sd-g@*)51f7)nc!a^3xeb(ma^9f6pm02_a+2h6tw^251fq"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# protegemos las rutas del servidor

ALLOWED_HOSTS = [
    "backendecuacion.onrender.com",
    "192.168.0.4",
    "127.0.0.1",
    "localhost",
    # coloca la red asiganda para pruebas univalle
]
# Application definition
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
    "django_otp.plugins.otp_static",  # códigos de respaldo
    "django_otp.plugins.otp_totp",  # TOTP (Authenticator)
    "two_factor",
]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
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
    # "GuardianUnivalle_Benito_Yucra.detectores.detector_sql.SQLIDefenseMiddleware",
    # "GuardianUnivalle_Benito_Yucra.detectores.detector_xss.XSSDefenseMiddleware",
    # "users.middleware.AuditoriaMiddleware",
]
LOGIN_URL = "two_factor:login"
LOGIN_REDIRECT_URL = "two_factor:profile"
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "benitoandrescalle035@gmail.com"
EMAIL_HOST_PASSWORD = "hmczrcgooenggoms"  # sin espacios
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


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
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
    "https://mallafinita.netlify.app",
    "https://*.netlify.app",
]
CORS_ALLOW_HEADERS = ["*"]
CSRF_TRUSTED_ORIGINS = ["https://mallafinita.netlify.app"]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()
APPEND_SLASH = True  # O False, según tu preferencia


# Configuraciones de seguridad para producción
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Auto primary key
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

# Archivos estáticos
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Archivos multimedia
MEDIA_URL = "/media/"
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUD_NAME", "dexggkhkd"),
    "API_KEY": os.getenv("CLOUDINARY_API_KEY", "896862494571978"),
    "API_SECRET": os.getenv("CLOUDINARY_API_SECRET", "-uWh6mQnL_5dUgI3LIE0rRYxVfI"),
    "SECURE": True,
}
# Configuration
cloudinary.config(
    cloud_name="dexggkhkd",
    api_key="896862494571978",
    api_secret="-uWh6mQnL_5dUgI3LIE0rRYxVfI",
    secure=True,
)
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# Lista de IPs confiables que no serán bloqueadas ni analizadas
SQLI_DEFENSE_TRUSTED_IPS = [
    "127.0.0.1",  # localhost
    "192.168.0.4",  # tu máquina interna, por ejemplo
    # coloca la red asiganda para pruebas univalle
]
XSS_DEFENSE_TRUSTED_IPS = [
    "127.0.0.1",
    "192.168.0.4",
]
XSS_DEFENSE_SANITIZE_INPUT = False  # True si quieres sanitizar automáticamente
XSS_DEFENSE_BLOCK = True  # Bloquear petición si se detecta XSS
XSS_DEFENSE_EXCLUDED_PATHS = ["/health", "/internal"]

# ejecuta este comando para probar el ataque en termux
# python manage.py runserver 0.0.0.0:8000
