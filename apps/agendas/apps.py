"""Configuração do app Django ``agendas``."""

from django.apps import AppConfig


class AgendasConfig(AppConfig):
    """App cliente HTTP do microserviço de agendas."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "agendas"
