"""Módulo serializers/relatorio_create."""
from __future__ import annotations
from typing import Any
from rest_framework import serializers
from ..models import Relatorio
from ..models.constants import TIPOS_RELATORIOS

class RelatorioCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de relatórios com validação de campos obrigatórios.

    O campo 'dados' não é validado no is_valid(), apenas setado no save().
    """
    usuario = serializers.CharField(required=True, help_text='RF do usuário')
    processo_uuid = serializers.UUIDField(required=True, help_text='UUID do processo')
    cabecalho = serializers.CharField(required=False, allow_blank=True, help_text='Cabeçalho do relatório (opcional)')
    agenda_uuid = serializers.CharField(required=False, allow_blank=True, help_text='UUID da agenda (opcional)')

    class Meta:
        """Define Meta."""
        model = Relatorio
        fields = ['tipo', 'usuario', 'processo_uuid', 'cabecalho', 'agenda_uuid']

    def validate_tipo(self, value: Any) -> Any:
        """Valida se o tipo do relatório é válido."""
        tipos_validos = [choice[0] for choice in TIPOS_RELATORIOS]
        if value not in tipos_validos:
            raise serializers.ValidationError(f'Tipo inválido. Tipos válidos: {', '.join(tipos_validos)}')
        return value

    def validate_cabecalho(self, value: str) -> str:
        """Se o cabeçalho vier apenas com tags HTML vazias (p/br/hX vazios),.

        considera vazio.
        Mantém o HTML quando houver texto de fato.
        """
        try:
            from django.utils.html import strip_tags as _strip
            texto = _strip(value or '').replace('&nbsp;', ' ').strip()
            if not texto:
                return ''
            return value
        except Exception:
            return value

    def save(self, dados: Any=None, **kwargs: Any) -> Any:
        """Salva o relatório no banco de dados.

        O campo 'dados' é setado aqui, não sendo validado no is_valid().

        Args:
            dados: Dados do relatório a serem salvos (opcional)
            **kwargs: Outros campos que podem ser passados (processo_uuid,
            cabecalho, etc.)
        """
        relatorio = super().save(**kwargs)
        if dados is not None:
            relatorio.dados = dados
            relatorio.save(update_fields=['dados'])
        return relatorio
