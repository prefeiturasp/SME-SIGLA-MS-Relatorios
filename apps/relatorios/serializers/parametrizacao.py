"""Módulo serializers/parametrizacao."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from rest_framework import serializers

from relatorios.models import Parametrizacao

DESCRICOES_PARAMETRIZACAO: dict[str, dict[str, Any]] = {
    "id": {"help_text": "Identificador numérico do registro."},
    "uuid": {
        "help_text": (
            "Identificador único do registro. É o valor que o frontend "
            "envia na rota de alteração."
        )
    },
    "criado_em": {"help_text": "Data e hora de criação do registro."},
    "atualizado_em": {
        "help_text": "Data e hora da última alteração do registro."
    },
    "cabecalho": {
        "help_text": (
            "Cabeçalho padrão, em HTML, exibido no topo de todos os "
            "relatórios. É gravado como enviado, sem filtro."
        )
    },
    "logo": {
        "help_text": (
            "Logotipo dos relatórios. No envio, é o arquivo de imagem, em "
            "`multipart/form-data`; em JSON só é aceito `null`, que remove "
            "o logotipo. Na resposta, é a URL da imagem, ou nulo. Só "
            "aparece nos relatórios do tipo que tem `usar_logotipo` ligado "
            "na personalização."
        )
    },
}


class ParametrizacaoSerializer(serializers.ModelSerializer):
    """Cabeçalho padrão e logotipo usados em todos os relatórios."""

    class Meta:
        """Representa os campos a serem serializados."""

        model = Parametrizacao
        fields = "__all__"
        read_only_fields = ["uuid", "criado_em", "atualizado_em"]
        extra_kwargs = DESCRICOES_PARAMETRIZACAO

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
