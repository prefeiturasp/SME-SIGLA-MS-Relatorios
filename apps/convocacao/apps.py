"""Configuração do app Django ``convocacao``."""

from django.apps import AppConfig


class ConvocacaoConfig(AppConfig):
    """App cliente HTTP dos microserviços de processos e convocação."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "convocacao"
