"""Configuração do app Django ``escolhas``."""

from django.apps import AppConfig


class EscolhasConfig(AppConfig):
    """App cliente HTTP do microserviço de escolhas."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "escolhas"
