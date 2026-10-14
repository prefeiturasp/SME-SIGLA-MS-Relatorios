"""Modelos das respostas da extração de dados.

Os blocos ``candidatos``, ``escolhas`` e ``concurso`` são repassados como
vieram do MS-Candidatos, do MS-Escolhas e do MS-Concursos; estes modelos
descrevem o que esses serviços devolvem hoje.
"""

from __future__ import annotations

from typing import Any, ClassVar

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from core.serializers import MapaComCamposSerializer


class _ChavesDaRespostaSerializer(serializers.Serializer):
    """Publica campos cuja chave real não é um identificador Python."""

    chaves: ClassVar[dict[str, str]] = {}

    def get_fields(self) -> dict[str, Any]:
        """Troca o nome declarado de cada campo pela chave da resposta."""
        return {
            self.chaves.get(nome, nome): campo
            for nome, campo in super().get_fields().items()
        }


class ContagemPorListaSerializer(serializers.Serializer):
    """Quantidade de candidatos, no total e por lista de classificação.

    O total pode ser maior que a soma das três listas, quando há registro
    sem lista identificada.
    """

    total = serializers.IntegerField(help_text="Quantidade total.")
    geral = serializers.IntegerField(help_text="Quantidade na lista geral.")
    pcd = serializers.IntegerField(
        help_text="Quantidade na lista de pessoas com deficiência (PCD)."
    )
    nna = serializers.IntegerField(
        help_text=(
            "Quantidade na lista de negros, negras e afrodescendentes "
            "(NNA)."
        )
    )


class FiltroAnoSerializer(serializers.Serializer):
    """Processos de convocação de um ano."""

    ano = serializers.IntegerField(
        help_text="Ano da data de convocação dos processos."
    )
    processo_uuids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text="UUIDs dos processos de convocação do ano.",
    )


class IndicadoresCandidatosSerializer(_ChavesDaRespostaSerializer):
    """Habilitados e convocados de um recorte, vindos do MS-Candidatos."""

    chaves = {"nao_convocados": "nao-convocados"}

    habilitados = ContagemPorListaSerializer(
        help_text=(
            "Habilitados do recorte: todos, na extração total; os dos "
            "processos do ano, no bloco de um ano."
        )
    )
    convocados = ContagemPorListaSerializer(
        help_text="Habilitados já convocados no recorte."
    )
    nao_convocados = ContagemPorListaSerializer(
        help_text=(
            "Habilitados do concurso (ou de todos os concursos, na "
            "extração total) menos os convocados do recorte."
        )
    )


class CandidatosPorAnoSerializer(MapaComCamposSerializer):
    """Indicadores de candidatos de um concurso, separados por ano.

    Além dos campos fixos, cada ano pedido é uma chave (por exemplo
    `2026`) com os indicadores daquele ano.
    """

    valor_das_chaves = IndicadoresCandidatosSerializer

    habilitados = ContagemPorListaSerializer(
        help_text="Habilitados do concurso, em todos os anos."
    )


class DreEscolhasSerializer(serializers.Serializer):
    """Escolhas e vagas de uma DRE."""

    nome = serializers.CharField(help_text="Nome da DRE.")
    escolhas = serializers.IntegerField(
        help_text="Escolhas de vaga realizadas em escolas da DRE."
    )
    vagas = serializers.IntegerField(
        help_text=(
            "Vagas ofertadas nas escolas da DRE, definitivas e precárias "
            "somadas."
        )
    )


class IndicadoresEscolhasSerializer(_ChavesDaRespostaSerializer):
    """Escolhas de um recorte por situação, vindas do MS-Escolhas."""

    chaves = {"nao_escolha": "nao-escolha"}

    escolha = ContagemPorListaSerializer(
        help_text="Candidatos que escolheram uma vaga."
    )
    nao_escolha = ContagemPorListaSerializer(
        help_text="Candidatos registrados como não escolha."
    )
    reconvocacao = ContagemPorListaSerializer(
        help_text="Candidatos registrados para reconvocação."
    )
    dres = DreEscolhasSerializer(
        many=True, help_text="Escolhas e vagas de cada DRE no recorte."
    )


class DreCargoEscolhasSerializer(serializers.Serializer):
    """Escolhas e vagas de uma DRE para um cargo."""

    nome = serializers.CharField(help_text="Nome da DRE.")
    escolhas = serializers.IntegerField(
        help_text="Escolhas de vaga realizadas na DRE para o cargo."
    )
    vagas = serializers.IntegerField(
        help_text=(
            "Vagas ofertadas na DRE para o cargo, definitivas e precárias "
            "somadas."
        )
    )
    codigo_cargo = serializers.IntegerField(
        help_text="Código numérico do cargo."
    )
    cargo_descricao = serializers.CharField(help_text="Nome do cargo.")
    ultima_escolha_em = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text=(
            "Data e hora da escolha mais recente na DRE para o cargo. "
            "Ausente quando há vagas, mas nenhuma escolha."
        ),
    )


DESCRICAO_DRES_CONCURSOS = (
    "Escolhas e vagas por DRE e cargo. Cada chave é o UUID de um concurso."
)
DESCRICAO_ULTIMA_ESCOLHA = (
    "Data e hora da escolha mais recente do recorte, ou nulo se não houve "
    "escolha."
)


class EscolhasTotalSerializer(IndicadoresEscolhasSerializer):
    """Escolhas de todos os concursos, vindas do MS-Escolhas."""

    dres_concursos = serializers.DictField(
        child=DreCargoEscolhasSerializer(many=True),
        help_text=DESCRICAO_DRES_CONCURSOS,
    )
    ultima_escolha_em = serializers.DateTimeField(
        allow_null=True, help_text=DESCRICAO_ULTIMA_ESCOLHA
    )


class EscolhasPorAnoSerializer(MapaComCamposSerializer):
    """Escolhas de um concurso, separadas por ano.

    Além dos campos fixos, cada ano pedido é uma chave (por exemplo
    `2026`) com as escolhas daquele ano.
    """

    valor_das_chaves = IndicadoresEscolhasSerializer

    concurso_uuid = serializers.UUIDField(help_text="UUID do concurso.")
    filtros = FiltroAnoSerializer(
        many=True,
        help_text="Anos pedidos, com os processos de cada um.",
    )
    dres_concursos = serializers.DictField(
        child=DreCargoEscolhasSerializer(many=True),
        help_text=DESCRICAO_DRES_CONCURSOS,
    )
    ultima_escolha_em = serializers.DateTimeField(
        allow_null=True, help_text=DESCRICAO_ULTIMA_ESCOLHA
    )


class CargoAutorizacoesSerializer(serializers.Serializer):
    """Autorizações publicadas de um cargo."""

    uuid = serializers.UUIDField(help_text="Identificador do cargo.")
    nome = serializers.CharField(help_text="Nome do cargo.")
    codigo = serializers.IntegerField(
        allow_null=True, help_text="Código numérico do cargo na SME."
    )
    autorizacoes = serializers.IntegerField(
        help_text="Soma das autorizações publicadas para o cargo no recorte."
    )
    data_autorizacao = serializers.DateField(
        help_text="Data da autorização mais recente do cargo no recorte."
    )


class AutorizacoesPublicadasSerializer(_ChavesDaRespostaSerializer):
    """Autorizações publicadas de um recorte, vindas do MS-Concursos."""

    chaves = {"autorizacoes_publicadas": "autorizacoes-publicadas"}

    autorizacoes_publicadas = serializers.IntegerField(
        help_text=(
            "Soma das autorizações publicadas no recorte. Inclui as "
            "autorizações sem cargo, que não aparecem em `cargos`."
        )
    )
    cargos = CargoAutorizacoesSerializer(
        many=True, help_text="Totais por cargo, em ordem alfabética do nome."
    )


class ComparativoIndicadoresSerializer(_ChavesDaRespostaSerializer):
    """Diferença de cada indicador: ano mais recente menos o mais antigo."""

    chaves = {
        "nao_convocados": "naoConvocados",
        "escolhas_realizadas": "escolhasRealizadas",
        "sem_escolha": "semEscolha",
    }

    convocados = serializers.FloatField(
        help_text="Diferença no total de convocados."
    )
    nao_convocados = serializers.FloatField(
        help_text="Diferença no total de não convocados."
    )
    escolhas_realizadas = serializers.FloatField(
        help_text="Diferença no total de escolhas de vaga."
    )
    reconvocacoes = serializers.FloatField(
        help_text="Diferença no total de reconvocações."
    )
    sem_escolha = serializers.FloatField(
        help_text="Diferença no total de não escolhas."
    )
    autorizacoes = serializers.FloatField(
        help_text="Diferença no total de autorizações publicadas."
    )


class ComparativoDreSerializer(_ChavesDaRespostaSerializer):
    """Diferença dos números de uma DRE entre os dois anos."""

    chaves = {"percentual_preenchimento": "percentualPreenchimento"}

    escolhas = serializers.FloatField(
        help_text="Diferença no número de escolhas."
    )
    vagas = serializers.FloatField(help_text="Diferença no número de vagas.")
    percentual_preenchimento = serializers.FloatField(
        help_text=(
            "Diferença, em pontos percentuais, da taxa de preenchimento "
            "(escolhas sobre vagas), com uma casa decimal."
        )
    )


class ComparativoSerializer(serializers.Serializer):
    """Comparação entre os dois anos pedidos."""

    anos = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=2,
        max_length=2,
        help_text="Os dois anos comparados, do mais antigo ao mais recente.",
    )
    indicadores = ComparativoIndicadoresSerializer(
        help_text="Diferença de cada indicador entre os dois anos."
    )
    dres = serializers.DictField(
        child=ComparativoDreSerializer(),
        help_text=(
            "Diferença por DRE. Cada chave é o nome da DRE sem o prefixo "
            "`DIRETORIA REGIONAL DE EDUCAÇÃO` ou `DRE`."
        ),
    )


@extend_schema_serializer(many=False)
class ExtracaoDadosSerializer(serializers.Serializer):
    """Indicadores de um concurso nos anos pedidos."""

    concurso_uuid = serializers.UUIDField(help_text="UUID do concurso.")
    filtros = FiltroAnoSerializer(
        many=True,
        help_text=(
            "Todos os anos em que o concurso tem processo de convocação, "
            "inclusive os que não foram pedidos."
        ),
    )
    candidatos = CandidatosPorAnoSerializer(
        help_text="Habilitados e convocados, como vieram do MS-Candidatos."
    )
    escolhas = EscolhasPorAnoSerializer(
        help_text="Escolhas e vagas, como vieram do MS-Escolhas."
    )
    concurso = serializers.DictField(
        child=AutorizacoesPublicadasSerializer(),
        help_text=(
            "Autorizações publicadas, como vieram do MS-Concursos. Cada "
            "chave é um ano pedido."
        ),
    )
    pendentes = serializers.DictField(
        child=ContagemPorListaSerializer(),
        help_text=(
            "Convocados que ainda não têm escolha, não escolha nem "
            "reconvocação registrada. Cada chave é um ano pedido."
        ),
    )
    comparativo = ComparativoSerializer(
        required=False,
        help_text="Só vem quando dois anos são pedidos.",
    )


class ExtracaoDadosTotalSerializer(serializers.Serializer):
    """Indicadores de todos os concursos e anos somados."""

    candidatos = IndicadoresCandidatosSerializer(
        help_text="Habilitados e convocados, como vieram do MS-Candidatos."
    )
    escolhas = EscolhasTotalSerializer(
        help_text="Escolhas e vagas, como vieram do MS-Escolhas."
    )
    concurso = AutorizacoesPublicadasSerializer(
        help_text="Autorizações publicadas, como vieram do MS-Concursos."
    )
    pendentes = ContagemPorListaSerializer(
        help_text=(
            "Convocados que ainda não têm escolha, não escolha nem "
            "reconvocação registrada."
        )
    )
