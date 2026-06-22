"""
Serializer para validação dos parâmetros de entrada da extração de dados.
"""

from rest_framework import serializers


class ExtracaoDadosQuerySerializer(serializers.Serializer):
    """Valida os query params do endpoint GET extracao-dados."""

    concurso_uuid = serializers.UUIDField(required=True)
    ano = serializers.ListField(
        child=serializers.IntegerField(min_value=1000, max_value=9999),
        min_length=1,
        max_length=2,
        allow_empty=False,
    )

    def to_internal_value(self, data):
        dados_modificados = data.dict() if hasattr(data, 'dict') else dict(data)
        ano_param = dados_modificados.get('ano')
        if isinstance(ano_param, str) and ano_param:
            dados_modificados['ano'] = ano_param.split(',')
        return super().to_internal_value(dados_modificados)
