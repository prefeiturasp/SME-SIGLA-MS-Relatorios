"""Módulo serializers/parametrizacao."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from rest_framework import serializers

from relatorios.models import Parametrizacao


class ParametrizacaoSerializer(serializers.ModelSerializer):
    """Serializer para serialização do modelo Parametrizacao."""

    class Meta:
        """Representa os campos a serem serializados."""

        model = Parametrizacao
        fields = "__all__"
        read_only_fields = ["uuid", "criado_em", "atualizado_em"]

    def to_representation(self, instance: Any) -> Any:
        """Monta a representação da parametrização com URL ajustada do logo."""
        data = super().to_representation(instance)
        logo = data.get("logo")
        if (
            logo
            and isinstance(logo, str)
            and settings.DJANGO_ENVIRONMENT != "local"
        ):
            base_prefix = settings.MS_PATH.rstrip("/")
            if base_prefix:
                segment = f"{base_prefix}/media/"
                if "/media/" in logo and segment not in logo:
                    data["logo"] = logo.replace("/media/", segment, 1)
        return data
