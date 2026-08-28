"""Configuração do app Django ``relatorios``."""

from django.apps import AppConfig


class RelatoriosConfig(AppConfig):
    """App de geração de relatórios de convocação."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "relatorios"
