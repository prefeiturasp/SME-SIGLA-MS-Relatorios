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

    @staticmethod
    def normalize_query_data(query_params) -> dict:
        """Normaliza query params repetidos (?ano=2025&ano=2026)."""
        return {
            "concurso_uuid": query_params.get("concurso_uuid"),
            "ano": query_params.getlist("ano"),
        }
