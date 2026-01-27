from rest_framework import serializers
from relatorios.models import Parametrizacao
from django.conf import settings


class ParametrizacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parametrizacao
        fields = '__all__'
        read_only_fields = ['uuid', 'criado_em', 'atualizado_em']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        logo = data.get('logo')
        if logo:
            if settings.DJANGO_ENVIRONMENT != 'local':
                base_prefix = settings.MS_PATH.rstrip('/')
                if base_prefix:
                    path = logo if logo.startswith('/') else f'/{logo}'
                    data['logo'] = f'{base_prefix}{path}'
        return data
