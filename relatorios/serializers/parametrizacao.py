from rest_framework import serializers
from relatorios.models import Parametrizacao


class ParametrizacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parametrizacao
        fields = '__all__'
        read_only_fields = ['uuid', 'criado_em', 'atualizado_em']

