"""Documentação OpenAPI das operações de parametrização."""

from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from core.openapi import (
    JSON,
    MULTIPART,
    exemplos_requisicao,
    parametro_ordenacao,
    resposta,
    respostas,
)
from core.serializers import ErroDetalheSerializer, ErrosValidacaoSerializer
from relatorios.serializers import ParametrizacaoSerializer

TAG_PARAMETRIZACAO = "Parametrização"

CABECALHO_EXEMPLO = (
    "<p>PREFEITURA DO MUNICÍPIO DE SÃO PAULO</p>"
    "<p>SECRETARIA MUNICIPAL DE EDUCAÇÃO</p>"
)

EXEMPLO_PARAMETRIZACAO = {
    "id": 1,
    "uuid": "3f5466c6-370c-45af-a48d-c6bad1b1027f",
    "criado_em": "2026-02-06T09:22:11.613781-03:00",
    "atualizado_em": "2026-09-20T11:00:02.482140-03:00",
    "cabecalho": CABECALHO_EXEMPLO,
    "logo": "http://localhost:8000/media/parametrizacao/logo.png",
}

REGISTRO_EM_USO = (
    "O `{id}` da rota é ignorado: a operação sempre usa o registro mais "
    "recente, que é o aplicado nos relatórios."
)

PARAMETRO_ID = OpenApiParameter(
    name="id",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.PATH,
    description=(
        "Ignorado. Qualquer valor serve, porque a operação sempre usa a "
        "parametrização mais recente. O frontend envia o `uuid` do registro."
    ),
)

CORPO_DA_ALTERACAO = {
    MULTIPART: ParametrizacaoSerializer,
    JSON: ParametrizacaoSerializer,
}

EXEMPLOS_DA_ALTERACAO = [
    *exemplos_requisicao(
        {
            "Trocar o logotipo": {"logo": "logo.png"},
            "Trocar o cabeçalho e o logotipo": {
                "cabecalho": CABECALHO_EXEMPLO,
                "logo": "logo.png",
            },
        },
        MULTIPART,
    ),
    *exemplos_requisicao(
        {
            "Trocar o cabeçalho": {"cabecalho": CABECALHO_EXEMPLO},
            "Remover o logotipo": {"logo": None},
        },
        JSON,
    ),
]

RESPOSTA_PARAMETRIZACAO = resposta(
    ParametrizacaoSerializer,
    "Parametrização depois da alteração.",
    {"Parametrização": EXEMPLO_PARAMETRIZACAO},
)

RESPOSTA_DADOS_INVALIDOS = resposta(
    ErrosValidacaoSerializer,
    "Arquivo que não é uma imagem válida ou campo com valor inválido.",
    {
        "Arquivo que não é imagem": {
            "logo": [
                "Fazer upload de uma imagem válida. O arquivo enviado não "
                "é um arquivo de imagem ou está corrompido."
            ]
        },
        "Logotipo enviado como texto": {
            "logo": [
                "O dado submetido não é um arquivo. Certifique-se do tipo "
                "de codificação no formulário."
            ]
        },
        "Cabeçalho nulo": {"cabecalho": ["Este campo não pode ser nulo."]},
    },
)

OPERACOES_PARAMETRIZACAO = {
    "list": extend_schema(
        operation_id="listar_parametrizacoes",
        summary="Listar parametrizações",
        description=(
            "Lista os registros de parametrização, do mais recente ao mais "
            "antigo, sem paginação. Os relatórios usam sempre o primeiro "
            "da lista.\n\n"
            "Em uso normal há um único registro: o serviço é instalado com "
            "ele, e as rotas de alteração nunca criam um segundo."
        ),
        parameters=[
            OpenApiParameter(name="search", exclude=True),
            parametro_ordenacao(
                [
                    "id",
                    "uuid",
                    "criado_em",
                    "atualizado_em",
                    "cabecalho",
                    "logo",
                ],
                "-criado_em",
            ),
        ],
        responses=respostas(
            {
                200: resposta(
                    ParametrizacaoSerializer(many=True),
                    "Registros de parametrização.",
                    {"Parametrização em uso": EXEMPLO_PARAMETRIZACAO},
                ),
            }
        ),
    ),
    "create": extend_schema(
        operation_id="criar_parametrizacao",
        summary="Criar parametrização (não disponível)",
        description=(
            "Responde sempre 405. A parametrização não é criada por esta "
            "rota: o registro é instalado com o serviço e alterado por "
            "`PUT` ou `PATCH`."
        ),
        request=None,
        responses=respostas(
            {
                405: resposta(
                    ErroDetalheSerializer,
                    "Criação não disponível.",
                    {
                        "Resposta fixa": {
                            "detail": 'Method "POST" not allowed.'
                        }
                    },
                ),
            }
        ),
    ),
    "retrieve": extend_schema(
        operation_id="detalhar_parametrizacao",
        summary="Consultar a parametrização em uso",
        description=(
            "Devolve o cabeçalho padrão e o logotipo aplicados nos "
            f"relatórios. {REGISTRO_EM_USO}\n\n"
            "Se não houver nenhum registro, o que só acontece quando o "
            "instalado com o serviço é apagado, a resposta é 200 apenas "
            "com `cabecalho` vazio e `logo` nulo."
        ),
        parameters=[PARAMETRO_ID],
        responses=respostas(
            {
                200: resposta(
                    ParametrizacaoSerializer,
                    "Parametrização em uso.",
                    {"Parametrização": EXEMPLO_PARAMETRIZACAO},
                ),
            }
        ),
    ),
    "update": extend_schema(
        operation_id="atualizar_parametrizacao",
        summary="Substituir a parametrização",
        description=(
            f"Altera o cabeçalho padrão e o logotipo. {REGISTRO_EM_USO}\n\n"
            "Nenhum campo é obrigatório, e o que não é enviado fica como "
            "está: na prática, a operação se comporta como o `PATCH`. Se "
            "não houver nenhum registro, cria um e responde 200."
        ),
        parameters=[PARAMETRO_ID],
        request=CORPO_DA_ALTERACAO,
        examples=EXEMPLOS_DA_ALTERACAO,
        responses=respostas(
            {200: RESPOSTA_PARAMETRIZACAO, 400: RESPOSTA_DADOS_INVALIDOS}
        ),
    ),
    "partial_update": extend_schema(
        operation_id="atualizar_parcial_parametrizacao",
        summary="Alterar a parametrização",
        description=(
            "Altera o cabeçalho padrão, o logotipo ou os dois. "
            f"{REGISTRO_EM_USO}\n\n"
            "Para enviar a imagem do logotipo, use `multipart/form-data`; "
            "o arquivo precisa ser uma imagem válida. Em JSON, `logo` só "
            "aceita `null`, que remove o logotipo; o campo vazio no "
            "formulário tem o mesmo efeito. O `cabecalho` é gravado como "
            "enviado, sem filtro de HTML.\n\n"
            "Na resposta, `logo` é a URL absoluta da imagem. Se não houver "
            "nenhum registro, a operação cria um e responde 200."
        ),
        parameters=[PARAMETRO_ID],
        request=CORPO_DA_ALTERACAO,
        examples=EXEMPLOS_DA_ALTERACAO,
        responses=respostas(
            {200: RESPOSTA_PARAMETRIZACAO, 400: RESPOSTA_DADOS_INVALIDOS}
        ),
    ),
}
