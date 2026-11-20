"""
Configuración de la maqueta SERVIEXPRESS (MAQUETA-SPEC.md, secciones 2 y 5.7).

Todo lo que cambia entre local y servidor se lee de variables de entorno:
DJANGO_SECRET_KEY, DJANGO_DEBUG, DJANGO_ALLOWED_HOSTS, DJANGO_CSRF_TRUSTED_ORIGINS
y DJANGO_DEMO.
"""

import os
from pathlib import Path

from django.contrib.messages import constants as mensajes


def _env_bool(nombre, por_defecto):
    return os.environ.get(nombre, por_defecto).strip().lower() in ("1", "true", "si", "sí", "yes")


def _env_lista(nombre, por_defecto=""):
    return [v.strip() for v in os.environ.get(nombre, por_defecto).split(",") if v.strip()]


BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = _env_bool("DJANGO_DEBUG", "1")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError("Falta la variable de entorno DJANGO_SECRET_KEY (obligatoria con DJANGO_DEBUG=0).")
    SECRET_KEY = "solo-desarrollo-local-no-usar-en-servidor"

ALLOWED_HOSTS = _env_lista("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1" if DEBUG else "")
CSRF_TRUSTED_ORIGINS = _env_lista("DJANGO_CSRF_TRUSTED_ORIGINS")

# Modo presentación de curso (sección 6): muestra la banda de aviso, los chips de trazabilidad
# HU/RF/CU y las credenciales demo en la pantalla de ingreso. Apagado, el sistema se ve como producto.
DEMO = _env_bool("DJANGO_DEMO", "0")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Apps del proyecto, en el orden de dependencias de la sección 4.
    "core",
    "cuentas",
    "personal",
    "clientes",
    "catalogo",
    "reservas",
    "abastecimiento",
    "ventas",
    "informes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "core.middleware.AvisoInactividadMiddleware",
    "informes.middleware.RegistroVisitasMiddleware",  # HU24
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.serviexpress",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# SQLite en local y en el VPS de prueba (sección 2).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Usuario propio, creado antes del primer migrate (sección 5.1).
AUTH_USER_MODEL = "cuentas.Usuario"
LOGIN_URL = "cuentas:ingresar"
LOGIN_REDIRECT_URL = "core:panel"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Localización (sección 2).
LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True


STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
# En el VPS los estáticos se copian fuera del home (nginx no puede leer /home/wadus): ver deploy/.
STATIC_ROOT = Path(os.environ.get("DJANGO_STATIC_ROOT", BASE_DIR / "staticfiles"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

MESSAGE_TAGS = {mensajes.ERROR: "danger"}


# RNF11: la sesión se cierra tras 15 minutos sin actividad.
SESSION_COOKIE_AGE = 15 * 60
SESSION_SAVE_EVERY_REQUEST = True  # la inactividad se cuenta desde la última acción


SERVIEXPRESS = {
    # DEMO: pendiente V07 (horario de atención no definido en el caso)
    "DIAS_ATENCION": [0, 1, 2, 3, 4, 5],  # lunes a sábado
    "HORA_INICIO": 9,
    "HORA_FIN": 18,  # último bloque empieza a las 17:00
    "DURACION_BLOQUE_MIN": 60,
    "RESERVAS_POR_BLOQUE": 1,
    "DIAS_ADELANTE_RESERVA": 30,
    # RNF10 y RNF11 (sí son requisitos)
    "MAX_INTENTOS_LOGIN": 5,
    "MINUTOS_BLOQUEO": 15,
}


# Producción: solo cuando DEBUG está apagado (sección 12).
if not DEBUG:
    SECURE_SSL_REDIRECT = _env_bool("DJANGO_SSL_REDIRECT", "1")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
