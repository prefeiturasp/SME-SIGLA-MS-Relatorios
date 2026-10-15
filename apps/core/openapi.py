"""Blocos compartilhados da documentação OpenAPI do microsserviço."""

from __future__ import annotations

from typing import Any

from django.db.models import Model
from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    Direction,
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
)

from core.serializers import (
    ErroDetalheSerializer,
    ErrosValidacaoSerializer,
    MapaComCamposSerializer,
)

JSON = "application/json"
MULTIPART = "multipart/form-data"
HTML = "text/html"
PDF = "application/pdf"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DOCX = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

TAMANHO_PAGINA_PADRAO = 10

UUID_PROCESSO_EXEMPLO = "c1a7e0d2-4b3f-4a6e-8d9c-0f1e2d3c4b5a"
UUID_CONCURSO_EXEMPLO = "7e6d5c4b-3a2f-4e1d-9c8b-7a6f5e4d3c2b"

MENSAGENS_DE_ERRO = {"type": "array", "items": {"type": "string"}}


class ErrosValidacaoExtension(OpenApiSerializerExtension):
    """Descreve ``ErrosValidacaoSerializer`` como mapa campo → mensagens."""

    target_class = ErrosValidacaoSerializer

    def map_serializer(
        self, auto_schema: AutoSchema, direction: Direction
    ) -> dict[str, Any]:
        """Retorna o schema do mapa de erros de validação."""
        return {
            "type": "object",
            "description": (
                "Erros de validação. Cada chave é o nome de um campo ou "
                "filtro inválido (ou `non_field_errors`) e o valor é a "
                "lista de mensagens. Em campos que são listas, o valor é "
                "um objeto em que cada chave é a posição do item inválido."
            ),
            "additionalProperties": {
                "oneOf": [
                    MENSAGENS_DE_ERRO,
                    {
                        "type": "object",
                        "additionalProperties": MENSAGENS_DE_ERRO,
                    },
                ]
            },
        }


class MapaComCamposExtension(OpenApiSerializerExtension):
    """Acrescenta as chaves variáveis ao modelo de um mapa com campos."""

    target_class = MapaComCamposSerializer
    match_subclasses = True

    def map_serializer(
        self, auto_schema: AutoSchema, direction: Direction
    ) -> dict[str, Any]:
        """Retorna os campos fixos mais o modelo das chaves variáveis."""
        esquema: dict[str, Any] = auto_schema._map_basic_serializer(
            self.target, direction
        )
        esquema["additionalProperties"] = auto_schema.resolve_serializer(
            self.target.valor_das_chaves, direction
        ).ref
        return esquema


def resposta(
    modelo: Any, descricao: str, exemplos: dict[str, Any] | None = None
) -> OpenApiResponse:
    """Monta uma resposta documentada com exemplos nomeados.

    Args:
        modelo: Serializer que descreve o corpo, ou ``None`` se não há corpo.
        descricao: Texto exibido para o código de resposta.
        exemplos: Valores de exemplo, indexados pelo nome do exemplo.

    Returns:
        Resposta pronta para o ``responses`` de ``extend_schema``.
    """
    return OpenApiResponse(
        response=modelo,
        description=descricao,
        examples=[
            OpenApiExample(nome, value=valor)
            for nome, valor in (exemplos or {}).items()
        ],
    )


def resposta_arquivo(
    descricao: str, tipo: str, exemplos: dict[str, str] | None = None
) -> OpenApiResponse:
    """Monta uma resposta cujo corpo é um arquivo.

    A chave da resposta em ``responses`` precisa ser ``(código, tipo)``,
    com o mesmo tipo de mídia informado aqui.

    Args:
        descricao: Texto exibido para o código de resposta.
        tipo: Tipo de mídia do arquivo.
        exemplos: Trechos do conteúdo, indexados pelo nome, quando o
            arquivo é texto. Sem exemplos, o corpo é tratado como binário.

    Returns:
        Resposta pronta para o ``responses`` de ``extend_schema``.
    """
    return OpenApiResponse(
        response=OpenApiTypes.STR if exemplos else OpenApiTypes.BINARY,
        description=descricao,
        examples=[
            OpenApiExample(nome, value=valor, media_type=tipo)
            for nome, valor in (exemplos or {}).items()
        ],
    )


def exemplos_requisicao(
    exemplos: dict[str, Any], tipo: str | None = None
) -> list[OpenApiExample]:
    """Monta exemplos nomeados para o corpo da requisição.

    Args:
        exemplos: Valores de exemplo, indexados pelo nome do exemplo.
        tipo: Tipo de mídia do corpo, quando a operação aceita mais de um.

    Returns:
        Exemplos prontos para o ``examples`` de ``extend_schema``.
    """
    return [
        OpenApiExample(nome, value=valor, request_only=True, media_type=tipo)
        for nome, valor in exemplos.items()
    ]


def resposta_nao_encontrado(modelo: type[Model]) -> OpenApiResponse:
    """Monta o 404 de uma rota de detalhe.

    Args:
        modelo: Model consultado pela rota; o nome dele aparece na mensagem.

    Returns:
        Resposta 404 com os textos devolvidos para identificador
        inexistente e para identificador malformado.
    """
    nome = modelo._meta.object_name
    return resposta(
        ErroDetalheSerializer,
        "Registro não encontrado.",
        {
            "Identificador inexistente": {
                "detail": f"No {nome} matches the given query."
            },
            "Identificador malformado": {"detail": "Não encontrado."},
        },
    )


def parametro_ordenacao(campos: list[str], padrao: str) -> OpenApiParameter:
    """Monta o parâmetro de query ``ordering``.

    Args:
        campos: Campos aceitos para ordenar.
        padrao: Ordenação aplicada quando o parâmetro não é enviado.

    Returns:
        Parâmetro de query com os campos aceitos na descrição.
    """
    aceitos = ", ".join(f"`{campo}`" for campo in campos)
    return OpenApiParameter(
        name="ordering",
        type=OpenApiTypes.STR,
        description=(
            f"Campo de ordenação: {aceitos}. Prefixe com `-` para ordem "
            f"decrescente. Padrão: `{padrao}`. Outros valores são ignorados."
        ),
    )


def parametro_busca(descricao: str) -> OpenApiParameter:
    """Monta o parâmetro de query ``search``.

    Args:
        descricao: Texto que diz onde a busca é feita.

    Returns:
        Parâmetro de query de busca textual.
    """
    return OpenApiParameter(
        name="search", type=OpenApiTypes.STR, description=descricao
    )


PARAMETRO_PAGINA = OpenApiParameter(
    name="page",
    type=OpenApiTypes.INT,
    description="Número da página, a partir de 1.",
)

PARAMETRO_TAMANHO_PAGINA = OpenApiParameter(
    name="page_size",
    type=OpenApiTypes.INT,
    description=(
        "Quantidade de registros por página. Padrão: "
        f"{TAMANHO_PAGINA_PADRAO}."
    ),
)

RESPOSTA_ACESSO_NEGADO = resposta(
    ErroDetalheSerializer,
    (
        "Credencial recusada: usuário e senha Basic incorretos ou, em "
        "chamada de escrita feita com a sessão do Django admin, falta do "
        "token CSRF. O serviço responde 403 nesses casos, e não 401. O "
        "`Authorization: Bearer` não é validado aqui e nunca causa esta "
        "resposta."
    ),
    {
        "Basic incorreto": {"detail": "Usuário ou senha inválido."},
        "Sessão sem CSRF": {"detail": "CSRF Failed: CSRF cookie not set."},
    },
)

RESPOSTA_PAGINA_INEXISTENTE = resposta(
    ErroDetalheSerializer,
    "Página além da última ou valor de `page` que não é um número.",
    {"Página inexistente": {"detail": "Página inválida."}},
)

RESPOSTA_ERRO_INTERNO = resposta(
    None,
    "Erro inesperado no servidor. O corpo é uma página HTML, não JSON.",
)

RESPOSTAS_COMUNS = {
    403: RESPOSTA_ACESSO_NEGADO,
    500: RESPOSTA_ERRO_INTERNO,
}


def _codigo(chave: Any) -> int:
    """Extrai o código HTTP de uma chave ``código`` ou ``(código, tipo)``."""
    return int(chave[0] if isinstance(chave, tuple) else chave)


def respostas(especificas: dict[Any, Any]) -> dict[Any, Any]:
    """Junta as respostas da operação às comuns a todo o microsserviço.

    Args:
        especificas: Respostas próprias da operação. A chave é o código
            HTTP ou, nas respostas em arquivo, ``(código, tipo de mídia)``.

    Returns:
        Respostas ordenadas por código, incluindo 403 e 500 quando a
        operação não define as suas. Chaves de um mesmo código mantêm a
        ordem em que foram declaradas.
    """
    proprios = {_codigo(chave) for chave in especificas}
    comuns = {
        codigo: valor
        for codigo, valor in RESPOSTAS_COMUNS.items()
        if codigo not in proprios
    }
    return dict(
        sorted(
            {**comuns, **especificas}.items(),
            key=lambda item: _codigo(item[0]),
        )
    )
