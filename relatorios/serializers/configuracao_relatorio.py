from rest_framework import serializers
from relatorios.models import ConfiguracaoRelatorio


class ConfiguracaoRelatorioSerializer(serializers.ModelSerializer):
    """Serializer para o modelo ConfiguracaoRelatorio."""

    class Meta:
        model = ConfiguracaoRelatorio
        fields = [
            'uuid',
            'tipo',
            'usar_logotipo',
            'usar_cabecalho_padrao',
            'cabecalho',
            'cabecalho_capa_ata',
            'texto_final',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['uuid']
