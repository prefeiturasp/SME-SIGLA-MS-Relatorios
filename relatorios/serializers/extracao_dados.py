"""
Serializer para validação dos parâmetros de entrada da extração de dados.
"""

from rest_framework import serializers


class ExtracaoDadosQuerySerializer(serializers.Serializer):
    """Valida os query params do endpoint GET extracao-dados."""

    concurso_uuid = serializers.UUIDField(required=True)
    ano = serializers.IntegerField(required=True, min_value=1000, max_value=9999)
