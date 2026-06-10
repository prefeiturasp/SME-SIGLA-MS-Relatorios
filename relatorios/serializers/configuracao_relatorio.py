"""Módulo serializers/configuracao_relatorio."""

from __future__ import annotations

import html
import re
from typing import Any

from django.utils.html import strip_tags
from rest_framework import serializers

from relatorios.models import ConfiguracaoRelatorio


def _sanitizar_html(value: Any) -> Any:
    """Sanitizar html.

    Args:
        value: Valor recebido para validação.

    Returns:
        Valor calculado conforme a regra aplicada.
    """
    if not value:
        return ""
    sem_atributos = re.sub("[\\w-]+=(['\\\"])[^'\\\"]*\\1>", "", value)
    texto_puro = html.unescape(strip_tags(sem_atributos)).strip()
    return sem_atributos if texto_puro else ""


class ConfiguracaoRelatorioSerializer(serializers.ModelSerializer):
    """Serializer para o modelo ConfiguracaoRelatorio."""

    class Meta:
        """Representa Meta."""

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
        """Validate cabecalho.

        Args:
            self: Instância do objeto.
            value: Valor recebido para validação.

        Returns:
            Valor validado do campo cabecalho.
        """
        return _sanitizar_html(value)

    def validate_cabecalho_gabarito(self, value: Any) -> Any:
        """Validate cabecalho gabarito.

        Args:
            self: Instância do objeto.
            value: Valor recebido para validação.

        Returns:
            Valor validado do campo cabecalho gabarito.
        """
        return _sanitizar_html(value)

    def validate_texto_final(self, value: Any) -> Any:
        """Validate texto final.

        Args:
            self: Instância do objeto.
            value: Valor recebido para validação.

        Returns:
            Valor validado do campo texto final.
        """
        return _sanitizar_html(value)
