"""Configuração do app Django ``core``."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """App com modelos e utilitários compartilhados."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
