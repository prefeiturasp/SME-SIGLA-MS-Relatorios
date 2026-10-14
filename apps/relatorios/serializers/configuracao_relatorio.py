"""Módulo serializers/configuracao_relatorio."""

from __future__ import annotations

import html
import re
from typing import Any

from django.utils.html import strip_tags
from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from relatorios.models import ConfiguracaoRelatorio
from relatorios.models.constants import TIPOS_RELATORIOS


def _sanitizar_html(value: Any) -> Any:
    """Remove tags e atributos perigosos do HTML informado."""
    if not value:
        return ""
    sem_atributos = re.sub("[\\w-]+=(['\\\"])[^'\\\"]*\\1>", "", value)
    texto_puro = html.unescape(strip_tags(sem_atributos)).strip()
    return sem_atributos if texto_puro else ""


FILTRO_DE_HTML = (
    "Passa pelo filtro de HTML descrito na operação de alteração, que "
    "corrompe tags com atributos."
)
SEM_PERSONALIZACAO = "Ausente quando nenhuma personalização atende à consulta."

DESCRICOES_PERSONALIZACAO: dict[str, dict[str, Any]] = {
    "uuid": {
        "help_text": (
            "Identificador da personalização, usado nas rotas de detalhe e "
            "de alteração."
        )
    },
    "tipo": {
        "help_text": (
            "Tipo de relatório a que os textos se aplicam. Cada tipo tem "
            "uma única personalização."
        )
    },
    "usar_logotipo": {
        "help_text": (
            "Se o logotipo da parametrização aparece nos relatórios deste "
            "tipo."
        )
    },
    "cabecalho": {
        "help_text": (
            "Cabeçalho do tipo, em HTML, exibido abaixo do cabeçalho "
            "padrão. Quando vazio, o relatório usa `cabecalho_gabarito`. "
            "Não é usado em `LISTAGEM_ESCOLHAS_DRES` nem em "
            f"`LISTA_CANDIDATOS_SESSAO`. {FILTRO_DE_HTML}"
        )
    },
    "cabecalho_gabarito": {
        "help_text": (
            "Cabeçalho sugerido para o tipo, em HTML. Entra no relatório "
            f"quando `cabecalho` está vazio. {FILTRO_DE_HTML}"
        )
    },
    "cabecalho_capa_ata": {
        "help_text": (
            "Texto da capa da Ata de Escolha, em HTML; só é usado em "
            "`ATA_ESCOLHA`. Aceita os marcadores `[[cargo]]` e "
            "`[[tipos_vagas]]`; qualquer outro sai no relatório como "
            "`[[ERRO: nome NÃO ENCONTRADO]]`. É gravado como enviado, sem "
            "filtro."
        )
    },
    "texto_final": {
        "help_text": (
            "Texto exibido ao final do relatório, em HTML. "
            f"{FILTRO_DE_HTML}"
        )
    },
    "criado_em": {"help_text": "Data e hora de criação do registro."},
    "atualizado_em": {
        "help_text": "Data e hora da última alteração do registro."
    },
}


def _descricao(campo: str) -> str:
    """Devolve a descrição publicada para um campo da personalização."""
    texto: str = DESCRICOES_PERSONALIZACAO[campo]["help_text"]
    return texto


class ConfiguracaoRelatorioSerializer(serializers.ModelSerializer):
    """Textos e opções de um tipo de relatório."""

    class Meta:
        """Representa os campos a serem serializados."""

        model = ConfiguracaoRelatorio
        fields = [
            "uuid",
            "tipo",
            "usar_logotipo",
            "cabecalho",
            "cabecalho_gabarito",
            "cabecalho_capa_ata",
            "texto_final",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["uuid"]
        extra_kwargs = DESCRICOES_PERSONALIZACAO

    def validate_cabecalho(self, value: Any) -> Any:
        """Valida cabecalho."""
        return _sanitizar_html(value)

    def validate_cabecalho_gabarito(self, value: Any) -> Any:
        """Valida cabecalho gabarito."""
        return _sanitizar_html(value)

    def validate_texto_final(self, value: Any) -> Any:
        """Valida texto final."""
        return _sanitizar_html(value)


# Só para a documentação: descreve o que ``PersonalizacaoViewSet.list``
# devolve, inclusive quando nenhuma personalização atende à consulta.
@extend_schema_serializer(many=False)
class PersonalizacaoConsultaSerializer(serializers.Serializer):
    """Personalização encontrada na consulta, ou um modelo em branco."""

    uuid = serializers.UUIDField(
        required=False,
        help_text=f"{_descricao('uuid')} {SEM_PERSONALIZACAO}",
    )
    tipo = serializers.ChoiceField(
        choices=TIPOS_RELATORIOS,
        allow_null=True,
        help_text=(
            f"{_descricao('tipo')} Nulo quando nenhuma personalização "
            "atende à consulta."
        ),
    )
    usar_logotipo = serializers.BooleanField(
        help_text=_descricao("usar_logotipo")
    )
    cabecalho = serializers.CharField(
        allow_blank=True, help_text=_descricao("cabecalho")
    )
    cabecalho_gabarito = serializers.CharField(
        allow_blank=True, help_text=_descricao("cabecalho_gabarito")
    )
    cabecalho_capa_ata = serializers.CharField(
        allow_blank=True, help_text=_descricao("cabecalho_capa_ata")
    )
    texto_final = serializers.CharField(
        allow_blank=True, help_text=_descricao("texto_final")
    )
    criado_em = serializers.DateTimeField(
        required=False,
        help_text=f"{_descricao('criado_em')} {SEM_PERSONALIZACAO}",
    )
    atualizado_em = serializers.DateTimeField(
        required=False,
        help_text=f"{_descricao('atualizado_em')} {SEM_PERSONALIZACAO}",
    )
