"""Configuração do app Django ``integracao``."""

from django.apps import AppConfig


class IntegracaoConfig(AppConfig):
    """App de infraestrutura compartilhada para clientes HTTP externos."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "integracao"
