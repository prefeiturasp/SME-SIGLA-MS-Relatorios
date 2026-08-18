"""Configuração do app Django ``concursos``."""

from django.apps import AppConfig


class ConcursosConfig(AppConfig):
    """App cliente HTTP do microserviço de concursos."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "concursos"
