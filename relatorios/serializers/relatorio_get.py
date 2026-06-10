"""Módulo serializers/relatorio_get."""

from rest_framework import serializers

from ..models import Relatorio


class RelatorioSerializer(serializers.ModelSerializer):
    """Serializer do modelo Relatorio."""

    class Meta:
        """Representa Meta."""

        model = Relatorio
        fields = "__all__"
