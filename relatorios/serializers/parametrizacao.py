from django.conf import settings
from rest_framework import serializers

from relatorios.models import Parametrizacao


class ParametrizacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parametrizacao
        fields = "__all__"
        read_only_fields = ["uuid", "criado_em", "atualizado_em"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        logo = data.get("logo")
        if logo and isinstance(logo, str):  # noqa: SIM102
            if settings.DJANGO_ENVIRONMENT != "local":
                base_prefix = settings.MS_PATH.rstrip("/")
                if base_prefix:
                    segment = f"{base_prefix}/media/"
                    # apenas prefixa a primeira ocorrência de /media/
                    if "/media/" in logo and segment not in logo:
                        data["logo"] = logo.replace("/media/", segment, 1)
        return data
