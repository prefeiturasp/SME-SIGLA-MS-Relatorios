"""Módulo serializers/relatorio_get."""
from rest_framework import serializers

from ..models import Relatorio


class RelatorioSerializer(serializers.ModelSerializer):
    """Define RelatorioSerializer."""
    class Meta:
        """Define Meta."""
        model = Relatorio
        fields = "__all__"
