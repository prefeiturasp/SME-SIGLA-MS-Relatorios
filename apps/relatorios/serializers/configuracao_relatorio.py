"""Módulo serializers/configuracao_relatorio."""

from __future__ import annotations

import html
import re
from typing import Any

from django.utils.html import strip_tags
from rest_framework import serializers

from relatorios.models import ConfiguracaoRelatorio


def _sanitizar_html(value: Any) -> Any:
    """Remove tags e atributos perigosos do HTML informado."""
    if not value:
        return ""
    sem_atributos = re.sub("[\\w-]+=(['\\\"])[^'\\\"]*\\1>", "", value)
    texto_puro = html.unescape(strip_tags(sem_atributos)).strip()
    return sem_atributos if texto_puro else ""


class ConfiguracaoRelatorioSerializer(serializers.ModelSerializer):
    """Serializer para serialização do modelo ConfiguracaoRelatorio."""

    class Meta:
        """Representa os campos a serem serializados."""

        model = ConfiguracaoRelatorio
        fields = [
            "uuid",
            "tipo",
            "usar_logotipo",
            "cabecalho",
            "cabecalho_gabarito",
            "cabecalho_capa_ata",
            "texto_final",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["uuid"]

    def validate_cabecalho(self, value: Any) -> Any:
        """Valida cabecalho."""
        return _sanitizar_html(value)

    def validate_cabecalho_gabarito(self, value: Any) -> Any:
        """Valida cabecalho gabarito."""
        return _sanitizar_html(value)

    def validate_texto_final(self, value: Any) -> Any:
        """Valida texto final."""
        return _sanitizar_html(value)
