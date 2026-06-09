"""Módulo serializers."""
from rest_framework import serializers

from .models import ConfiguracaoRelatorio, Relatorio


class RelatorioSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Relatorio."""

    class Meta:
        """Define Meta."""
        model = Relatorio
        fields = [
            "uuid",
            "nome",
            "tipo",
            "usuario",
            "processo_uuid",
            "agenda_uuid",
            "cabecalho",
            "usou_cabecalho_padrao",
            "usou_logotipo",
            "texto_final",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["uuid"]


class ConfiguracaoRelatorioSerializer(serializers.ModelSerializer):
    """Serializer para o modelo ConfiguracaoRelatorio."""

    class Meta:
        """Define Meta."""
        model = ConfiguracaoRelatorio
        fields = [
            "uuid",
            "tipo",
            "usar_logotipo",
            "usar_cabecalho_padrao",
            "cabecalho",
            "texto_final",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["uuid"]
