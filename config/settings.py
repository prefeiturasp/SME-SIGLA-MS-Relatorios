"""
Django settings for convocacao_processes project.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DJANGO_ENVIRONMENT = os.environ.get("DJANGO_ENVIRONMENT", "local")
AMBIENTE_APLICACAO = os.environ.get("AMBIENTE_APLICACAO", DJANGO_ENVIRONMENT)
MS_PATH = os.environ.get("MS_PATH", "/ms-relatorios")

BASE_DIR = Path(__file__).resolve().parent.parent

sys.path.insert(0, os.path.join(BASE_DIR, "apps"))
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-your-secret-key-here"
)
DEBUG = True#os.environ.get("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "qa-api-sigla.sme.prefeitura.sp.gov.br",
    "hom-api-sigla.sme.prefeitura.sp.gov.br",
]
CSRF_TRUSTED_ORIGINS = [
    "https://qa-api-sigla.sme.prefeitura.sp.gov.br",
    "https://hom-api-sigla.sme.prefeitura.sp.gov.br",
]

# Application definition
INSTALLED_APPS = [
    "elasticapm.contrib.django",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "django_filters",
    "auditlog",
    "drf_spectacular",
    "core",
    "relatorios",
]

MIDDLEWARE = [
    "elasticapm.contrib.django.middleware.TracingMiddleware",
    "sigla_sdk.middlewares.CorrelationIdMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "sigla_sdk.middlewares.AuditlogJWTMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

# Database
DB_ENGINE = os.environ.get("DB_ENGINE", "django.db.backends.postgresql")

if DB_ENGINE == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": os.environ.get("DB_NAME", BASE_DIR / "db.sqlite3"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": os.environ.get("DB_NAME", "db_sigla"),
            "USER": os.environ.get("DB_USER", "postgres"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "postgres"),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }

# Password validation
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
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

_ms_path_segment = (MS_PATH or "/ms-relatorios").strip("/")
if DJANGO_ENVIRONMENT != "local":
    STATIC_URL = f"/{_ms_path_segment}/django_static/"
    MEDIA_URL = f"/{_ms_path_segment}/media/"
else:
    STATIC_URL = "/django_static/"
    MEDIA_URL = "/media/"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# DRF settings
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        # "sigla_sdk.autenticacao.authentication.ApiKeyAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# AuditLog settings
AUDITLOG_INCLUDE_ALL_MODELS = False

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "sigla_sdk.logging.json_formatter.CustomJsonFormatter",
            # Estes campos do logging padrão virarão chaves no JSON
            "format": "%(levelname)s %(asctime)s %(module)s %(filename)s %(lineno)d %(funcName)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "elasticapm": {
            "level": "DEBUG",
            "class": "elasticapm.contrib.django.handlers.LoggingHandler",
        },
    },
    "loggers": {
        # Logger do Django (Framework)
        "django": {
            "handlers": ["console", "elasticapm"],
            "level": "INFO",
            "propagate": False,
        },
        # Seu Logger de Aplicação (substitua pelo nome do seu app)
        "relatorios": {
            "handlers": ["console", "elasticapm"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["console", "elasticapm"],
            "level": "ERROR",  # Alterando para ERROR, ele para de mostrar os GET/POST/OPTIONS de rotina (INFO)
            "propagate": False,
        },
        "elasticapm.errors": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": False,
        },
        "elasticapm.logging": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

ELASTIC_APM = {
    "SERVICE_NAME": os.environ.get(
        "ELASTIC_APM_SERVICE_NAME", "SME-SIGLA-MS-Relatorios"
    ),
    "SECRET_TOKEN": os.environ.get("ELASTIC_APM_SECRET_TOKEN", ""),
    "SERVER_URL": os.environ.get(
        "ELASTIC_APM_SERVER_URL", "http://localhost:8200"
    ),
    "SERVER_TIMEOUT": os.environ.get("ELASTIC_APM_SERVER_TIMEOUT", "35s"),
    "ENVIRONMENT": os.environ.get(
        "ELASTIC_APM_ENVIRONMENT", AMBIENTE_APLICACAO
    ),
    "ENABLED": os.environ.get("ELASTIC_APM_ENABLED", "0") == "1",
    "RECORDING": True,
    "CAPTURE_BODY": os.environ.get("ELASTIC_APM_CAPTURE_BODY", "all"),
    "CAPTURE_HEADERS": os.environ.get("ELASTIC_APM_CAPTURE_HEADERS", "1")
    == "1",
    "TRANSACTION_SAMPLE_RATE": float(
        os.environ.get("ELASTIC_APM_TRANSACTION_SAMPLE_RATE", "0.3")
    ),
    "METRICS_INTERVAL": os.environ.get("ELASTIC_APM_METRICS_INTERVAL", "10s"),
    "FLUSH_INTERVAL": os.environ.get("ELASTIC_APM_FLUSH_INTERVAL", "10s"),
    "MAX_BATCH_EVENT_COUNT": int(
        os.environ.get("ELASTIC_APM_MAX_BATCH_EVENT_COUNT", "1000")
    ),
    "MAX_QUEUE_EVENT_COUNT": int(
        os.environ.get("ELASTIC_APM_MAX_QUEUE_EVENT_COUNT", "1000")
    ),
    "TRANSACTION_MAX_SPANS": int(
        os.environ.get("ELASTIC_APM_TRANSACTION_MAX_SPANS", "500")
    ),
    "DJANGO_TRANSACTION_NAME_FROM_ROUTE": True,
    "LOG_LEVEL": os.environ.get("ELASTIC_APM_LOG_LEVEL", "INFO"),
    "LOG_ECS_REFORMATTING": os.environ.get(
        "ELASTIC_APM_LOG_ECS_REFORMATTING", "off"
    ),
    'RECORDING': True,               # Garante que o APM está ativo
    'TRANSACTIONS_ROOT_UNNAMED': True, # Captura rotas mesmo se não tiverem nome definido nas URLs
    'CAPTURE_BODY': 'all',
    'CAPTURE_HEADERS': True,
    'CAPTURE_ERRORS': True,
    'CAPTURE_PERFORMANCE': True,
    'CAPTURE_TRANSACTIONS': True,
    'CAPTURE_SPANS': True,
    'CAPTURE_TRANSACTION_STACKTRACES': True,
    'CAPTURE_TRANSACTION_STACKTRACES_LIMIT': 10,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Relatorios Sigla API",
    "DESCRIPTION": "API para o sistema de relatórios de sigla",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# External services configuration
PROCESSOS_API_URL = os.environ.get(
    "PROCESSOS_API_URL", "http://localhost:8000"
)
PROCESSOS_API_KEY = os.environ.get("PROCESSOS_API_KEY", "api-key-processos")

ESCOLHAS_API_URL = os.environ.get("ESCOLHAS_API_URL", "http://localhost:8004")
ESCOLHAS_API_KEY = os.environ.get("ESCOLHAS_API_KEY", "api-key-escolhas")

CONVOCACAO_API_URL = os.environ.get(
    "CONVOCACAO_API_URL", "http://localhost:8000"
)
CONVOCACAO_API_KEY = os.environ.get("CONVOCACAO_API_KEY", "api-key-convocacao")

CANDIDATOS_API_URL = os.environ.get(
    "CANDIDATOS_API_URL", "http://localhost:8002"
)
CANDIDATOS_API_KEY = os.environ.get("CANDIDATOS_API_KEY", "api-key-candidatos")

CONCURSOS_API_URL = os.environ.get(
    "CONCURSOS_API_URL", "http://localhost:8001"
)
CONCURSOS_API_KEY = os.environ.get("CONCURSOS_API_KEY", "api-key-concursos")

AGENDAS_API_URL = os.environ.get("AGENDAS_API_URL", "http://localhost:8005")
AGENDAS_API_KEY = os.environ.get("AGENDAS_API_KEY", "api-key-agendas")

# API Key (autenticação entre microsserviços)
API_KEY = os.environ.get("API_KEY", "api-key-relatorios")
API_KEY_HEADER = os.environ.get("API_KEY_HEADER", "X-API-Key")

# Relatórios configuration
RELATORIO_CABECALHO_PADRAO = (
    "PREFEITURA DO MUNICÍPIO DE SÃO PAULO\n"
    "SECRETARIA MUNICIPAL DE EDUCAÇÃO\n"
    "DIVISÃO DE GESTÃO DE CARREIRAS - COGEP"
)
