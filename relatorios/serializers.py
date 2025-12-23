from rest_framework import serializers
from .models import Relatorio

class RelatorioSerializer(serializers.ModelSerializer):
    """Serializer para o modelo Relatorio."""
    
    class Meta:
        model = Relatorio
        fields = [
            'uuid',
            'nome',
            'tipo',
            'criado_em',
            'atualizado_em',
        ]
        read_only_fields = ['uuid']