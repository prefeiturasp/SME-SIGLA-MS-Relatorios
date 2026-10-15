"""Módulo serializers/relatorio_get."""

from typing import Any

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from relatorios.models import Relatorio

NAO_PREENCHIDO_NA_GERACAO = (
    "A geração de relatório não preenche este campo; ele só muda por `PUT` "
    "ou `PATCH`."
)

DESCRICOES_RELATORIO: dict[str, dict[str, Any]] = {
    "id": {
        "help_text": (
            "Identificador numérico do registro, usado nas rotas de detalhe."
        )
    },
    "uuid": {"help_text": "Identificador único do registro."},
    "criado_em": {"help_text": "Data e hora em que o relatório foi gerado."},
    "atualizado_em": {
        "help_text": "Data e hora da última alteração do registro."
    },
    "tipo": {"help_text": "Tipo do relatório gerado."},
    "usuario": {"help_text": "RF do usuário que pediu o relatório."},
    "dados": {
        "help_text": (
            "Dados usados para montar o relatório, reunidos dos outros "
            "microsserviços. O formato é próprio de cada tipo: lista de "
            "cargos em alguns, objeto em outros."
        )
    },
    "processo_uuid": {"help_text": "UUID do processo de convocação."},
    "cabecalho": {
        "help_text": (
            "Cabeçalho informado no pedido de geração. Não é o cabeçalho "
            "que saiu no relatório."
        )
    },
    "agenda_uuid": {
        "help_text": "UUID da agenda informada no pedido, ou nulo."
    },
    "usou_cabecalho_padrao": {
        "help_text": (
            "Se o relatório usou o cabeçalho padrão. "
            f"{NAO_PREENCHIDO_NA_GERACAO}"
        )
    },
    "usou_logotipo": {
        "help_text": (
            f"Se o relatório usou o logotipo. {NAO_PREENCHIDO_NA_GERACAO}"
        )
    },
    "texto_final": {
        "help_text": f"Texto final do relatório. {NAO_PREENCHIDO_NA_GERACAO}"
    },
    "cabecalho_capa_ata": {
        "help_text": (
            f"Texto da capa da Ata de Escolha. {NAO_PREENCHIDO_NA_GERACAO}"
        )
    },
}


class RelatorioSerializer(serializers.ModelSerializer):
    """Registro do histórico de relatórios gerados."""

    class Meta:
        """Representa Meta."""

        model = Relatorio
        fields = "__all__"
        extra_kwargs = DESCRICOES_RELATORIO


# Os dois modelos abaixo só descrevem, para a documentação, o envelope que
# ``relatorios.utils.CustomPagination`` monta.
class LinksPaginacaoSerializer(serializers.Serializer):
    """Links de navegação entre as páginas da listagem."""

    next = serializers.URLField(
        allow_null=True,
        help_text="URL da próxima página, ou nulo na última página.",
    )
    previous = serializers.URLField(
        allow_null=True,
        help_text="URL da página anterior, ou nulo na primeira página.",
    )


@extend_schema_serializer(many=False)
class RelatorioPaginadoSerializer(serializers.Serializer):
    """Página do histórico de relatórios gerados."""

    links = LinksPaginacaoSerializer(
        help_text="Links para as páginas vizinhas."
    )
    count = serializers.IntegerField(
        help_text="Total de registros que atendem aos filtros."
    )
    page = serializers.IntegerField(help_text="Número da página retornada.")
    page_size = serializers.IntegerField(
        help_text=(
            "Valor de `page_size` recebido na consulta, ou o padrão quando "
            "ele não é enviado."
        )
    )
    results = RelatorioSerializer(many=True, help_text="Registros da página.")
