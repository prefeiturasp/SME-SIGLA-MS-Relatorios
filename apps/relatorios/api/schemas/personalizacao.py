"""Documentação OpenAPI das operações de personalização por tipo."""

from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from core.openapi import (
    JSON,
    exemplos_requisicao,
    parametro_busca,
    resposta,
    resposta_nao_encontrado,
    respostas,
)
from core.serializers import ErrosValidacaoSerializer
from relatorios.models import ConfiguracaoRelatorio
from relatorios.models.constants import TIPOS_RELATORIOS
from relatorios.serializers import (
    ConfiguracaoRelatorioSerializer,
    PersonalizacaoConsultaSerializer,
)

TAG_PERSONALIZACAO = "Personalização"

TEXTO_FINAL_EXEMPLO = "<p>São Paulo, 20 de setembro de 2026.</p>"
CABECALHO_EXEMPLO = "<p>Lauda de <strong>vagas</strong></p>"

EXEMPLO_PERSONALIZACAO = {
    "uuid": "b318ce94-1e19-4bd8-8eef-8ac53247ac76",
    "tipo": "LAUDA_VAGAS",
    "usar_logotipo": True,
    "cabecalho": CABECALHO_EXEMPLO,
    "cabecalho_gabarito": "",
    "cabecalho_capa_ata": "",
    "texto_final": TEXTO_FINAL_EXEMPLO,
    "criado_em": "2026-02-06T09:22:11.654244-03:00",
    "atualizado_em": "2026-09-20T11:00:02.637801-03:00",
}

EXEMPLO_EM_BRANCO = {
    "tipo": None,
    "usar_logotipo": False,
    "cabecalho": "",
    "cabecalho_gabarito": "",
    "cabecalho_capa_ata": "",
    "texto_final": "",
}

TEXTOS_E_FILTRO = (
    "Onde cada texto aparece (conferido no HTML dos 10 tipos):\n\n"
    "| Campo | Aparece |\n"
    "|---|---|\n"
    "| `cabecalho` | Abaixo do cabeçalho padrão da parametrização, em "
    "todos os tipos menos `LISTAGEM_ESCOLHAS_DRES` e "
    "`LISTA_CANDIDATOS_SESSAO` |\n"
    "| `cabecalho_gabarito` | No lugar de `cabecalho`, quando ele está "
    "vazio |\n"
    "| `texto_final` | No fim do relatório, em todos os tipos |\n"
    "| `cabecalho_capa_ata` | Na capa da Ata de Escolha |\n\n"
    "**Filtro de HTML.** `cabecalho`, `cabecalho_gabarito` e `texto_final` "
    "passam por um filtro antes de gravar. Ele apaga o último atributo de "
    "cada tag junto com o `>` que a fecha, o que corrompe a tag:\n\n"
    "| Enviado | Gravado |\n"
    "|---|---|\n"
    "| `<p>Texto simples</p>` | `<p>Texto simples</p>` |\n"
    '| `<p class="ql-align-center">TEXTO</p>` | vazio |\n'
    '| `<p class="ql-align-center"><strong>COGEP</strong></p><p>Lauda</p>` '
    "| `<p <strong>COGEP</strong></p><p>Lauda</p>` |\n\n"
    "HTML sem atributos é gravado como enviado. Se, sem as tags, não sobra "
    "texto (por exemplo `<p><br></p>`), o campo é gravado vazio. "
    "`cabecalho_capa_ata` não passa pelo filtro.\n\n"
    "**Capa da Ata.** `cabecalho_capa_ata` aceita os marcadores "
    "`[[cargo]]`, trocado pelo nome do cargo da ata, e `[[tipos_vagas]]`, "
    "trocado sempre por `PRECÁRIAS/DEFINITIVAS`. Qualquer outro marcador "
    "sai no relatório como `[[ERRO: nome NÃO ENCONTRADO]]`."
)

PARAMETRO_UUID = OpenApiParameter(
    name="uuid",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.PATH,
    description=(
        "UUID da personalização, devolvido na consulta por tipo de "
        "relatório."
    ),
)

PARAMETROS_CONSULTA = [
    OpenApiParameter(
        name="tipo",
        type=OpenApiTypes.STR,
        enum=[tipo for tipo, _ in TIPOS_RELATORIOS],
        description=(
            "Tipo de relatório cuja personalização se quer. Sem ele, vem a "
            "personalização criada mais recentemente, de qualquer tipo."
        ),
    ),
    parametro_busca(
        "Busca por trecho do tipo, por exemplo `LAUDA`. A resposta é a "
        "primeira personalização encontrada."
    ),
    OpenApiParameter(
        name="ordering",
        type=OpenApiTypes.STR,
        enum=["criado_em", "-criado_em"],
        description=(
            "Qual personalização vem quando mais de uma atende à consulta: "
            "`-criado_em`, a criada mais recentemente (padrão), ou "
            "`criado_em`, a mais antiga."
        ),
    ),
]

RESPOSTA_PERSONALIZACAO = resposta(
    ConfiguracaoRelatorioSerializer,
    "Personalização depois da alteração.",
    {"Lauda de vagas": EXEMPLO_PERSONALIZACAO},
)

RESPOSTA_NAO_ENCONTRADA = resposta_nao_encontrado(ConfiguracaoRelatorio)

DADOS_INVALIDOS = (
    "Campo com valor inválido ou `tipo` que já tem personalização."
)

VALORES_INVALIDOS = {
    "Tipo já personalizado": {
        "tipo": [
            "Configuração de Relatório com este Tipo de Relatório já existe."
        ]
    },
    "Tipo inexistente": {"tipo": ['"XYZ" não é um escolha válido.']},
    "Opção que não é booleana": {
        "usar_logotipo": ["Must be a valid boolean."]
    },
    "Texto nulo": {"cabecalho": ["Este campo não pode ser nulo."]},
}

OPERACOES_PERSONALIZACAO = {
    "list": extend_schema(
        operation_id="consultar_personalizacao",
        summary="Consultar a personalização de um tipo de relatório",
        description=(
            "Devolve **uma** personalização, e não uma lista: a primeira "
            "que atende à consulta. Use `tipo` para pedir a de um tipo de "
            "relatório, que é como o frontend chama.\n\n"
            "Quando nenhuma personalização atende à consulta, a resposta "
            "ainda é 200, com um modelo em branco: `tipo` nulo, textos "
            "vazios e sem `uuid` nem datas.\n\n"
            "O serviço é instalado com uma personalização para cada tipo. "
            "Existem também três registros antigos, de tipos que saíram "
            "das opções (`RESULTADO_ESCOLHA_SIM`, `RESULTADO_ESCOLHA_NAO` "
            "e `RESULTADO_ESCOLHA_RECONVOCACAO`). Eles não podem ser "
            "pedidos por `tipo`, mas aparecem na busca por `search`, e "
            "então `tipo` vem com um valor fora das opções."
        ),
        parameters=PARAMETROS_CONSULTA,
        responses=respostas(
            {
                200: resposta(
                    PersonalizacaoConsultaSerializer,
                    "Personalização encontrada, ou o modelo em branco.",
                    {
                        "Personalização do tipo": EXEMPLO_PERSONALIZACAO,
                        "Nenhuma encontrada": EXEMPLO_EM_BRANCO,
                    },
                ),
                400: resposta(
                    ErrosValidacaoSerializer,
                    "Filtro `tipo` com valor fora das opções.",
                    {
                        "Tipo inexistente": {
                            "tipo": [
                                "Faça uma escolha válida. XYZ não é uma "
                                "das escolhas disponíveis."
                            ]
                        }
                    },
                ),
            }
        ),
    ),
    "retrieve": extend_schema(
        operation_id="detalhar_personalizacao",
        summary="Detalhar personalização",
        description=(
            "Devolve a personalização identificada pelo `uuid`. Nos três "
            "registros antigos citados na consulta por tipo, `tipo` vem "
            "com um valor fora das opções."
        ),
        parameters=[PARAMETRO_UUID],
        responses=respostas(
            {
                200: resposta(
                    ConfiguracaoRelatorioSerializer,
                    "Personalização.",
                    {"Lauda de vagas": EXEMPLO_PERSONALIZACAO},
                ),
                404: RESPOSTA_NAO_ENCONTRADA,
            }
        ),
    ),
    "update": extend_schema(
        operation_id="atualizar_personalizacao",
        summary="Substituir personalização",
        description=(
            "Altera os textos e as opções de um tipo de relatório, como o "
            "`PATCH`, exigindo `tipo`. Os demais campos não são "
            "obrigatórios, e o que não é enviado fica como está.\n\n"
            f"{TEXTOS_E_FILTRO}"
        ),
        parameters=[PARAMETRO_UUID],
        request={JSON: ConfiguracaoRelatorioSerializer},
        examples=exemplos_requisicao(
            {
                "Todos os campos": {
                    "tipo": "LAUDA_VAGAS",
                    "usar_logotipo": True,
                    "cabecalho": CABECALHO_EXEMPLO,
                    "cabecalho_gabarito": "",
                    "cabecalho_capa_ata": "",
                    "texto_final": TEXTO_FINAL_EXEMPLO,
                }
            }
        ),
        responses=respostas(
            {
                200: RESPOSTA_PERSONALIZACAO,
                400: resposta(
                    ErrosValidacaoSerializer,
                    f"`tipo` ausente. {DADOS_INVALIDOS}",
                    {
                        "Tipo ausente": {
                            "tipo": ["Este campo é obrigatório."]
                        },
                        **VALORES_INVALIDOS,
                    },
                ),
                404: RESPOSTA_NAO_ENCONTRADA,
            }
        ),
    ),
    "partial_update": extend_schema(
        operation_id="atualizar_parcial_personalizacao",
        summary="Alterar personalização",
        description=(
            "Altera os textos e as opções de um tipo de relatório. Só os "
            "campos enviados mudam. `tipo` pode ser trocado, mas não para "
            "um tipo que já tem personalização; `uuid` e as datas são "
            "ignorados se enviados.\n\n"
            f"{TEXTOS_E_FILTRO}"
        ),
        parameters=[PARAMETRO_UUID],
        request={JSON: ConfiguracaoRelatorioSerializer},
        examples=exemplos_requisicao(
            {
                "Cabeçalho, texto final e logotipo": {
                    "usar_logotipo": True,
                    "cabecalho": CABECALHO_EXEMPLO,
                    "texto_final": TEXTO_FINAL_EXEMPLO,
                },
                "Capa da Ata com marcadores": {
                    "cabecalho_capa_ata": (
                        "<p>Escolha de vagas [[tipos_vagas]] para o cargo "
                        "de [[cargo]].</p>"
                    )
                },
            }
        ),
        responses=respostas(
            {
                200: RESPOSTA_PERSONALIZACAO,
                400: resposta(
                    ErrosValidacaoSerializer,
                    DADOS_INVALIDOS,
                    VALORES_INVALIDOS,
                ),
                404: RESPOSTA_NAO_ENCONTRADA,
            }
        ),
    ),
}
