"""Módulo serializers/configuracao_relatorio."""
from __future__ import annotations
from typing import Any
import html
import re
from django.utils.html import strip_tags
from rest_framework import serializers
from relatorios.models import ConfiguracaoRelatorio

def _sanitizar_html(value: Any) -> Any:
    """Executa  sanitizar html."""
    if not value:
        return ''
    sem_atributos = re.sub('[\\w-]+=([\'\\"])[^\'\\"]*\\1>', '', value)
    texto_puro = html.unescape(strip_tags(sem_atributos)).strip()
    return sem_atributos if texto_puro else ''

class ConfiguracaoRelatorioSerializer(serializers.ModelSerializer):
    """Serializer para o modelo ConfiguracaoRelatorio."""

    class Meta:
        """Define Meta."""
        model = ConfiguracaoRelatorio
        fields = ['uuid', 'tipo', 'usar_logotipo', 'cabecalho', 'cabecalho_gabarito', 'cabecalho_capa_ata', 'texto_final', 'criado_em', 'atualizado_em']
        read_only_fields = ['uuid']

    def validate_cabecalho(self, value: Any) -> Any:
        """Executa validate cabecalho."""
        return _sanitizar_html(value)

    def validate_cabecalho_gabarito(self, value: Any) -> Any:
        """Executa validate cabecalho gabarito."""
        return _sanitizar_html(value)

    def validate_texto_final(self, value: Any) -> Any:
        """Executa validate texto final."""
        return _sanitizar_html(value)
