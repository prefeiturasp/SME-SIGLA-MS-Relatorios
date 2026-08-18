"""Configuração do app Django ``candidatos``."""

from django.apps import AppConfig


class CandidatosConfig(AppConfig):
    """App cliente HTTP do microserviço de candidatos."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "candidatos"
