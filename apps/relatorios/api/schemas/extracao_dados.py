"""Documentação OpenAPI das operações de extração de dados."""

from __future__ import annotations

from typing import Any

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from core.openapi import (
    UUID_CONCURSO_EXEMPLO,
    UUID_PROCESSO_EXEMPLO,
    resposta,
    respostas,
)
from core.serializers import ErroDetalheSerializer, ErrosValidacaoSerializer
from relatorios.serializers import (
    ExtracaoDadosSerializer,
    ExtracaoDadosTotalSerializer,
)

TAG_EXTRACAO_DADOS = "Extração de dados"

DRE_BUTANTA = "DIRETORIA REGIONAL DE EDUCACAO BUTANTA"
DRE_IPIRANGA = "DIRETORIA REGIONAL DE EDUCACAO IPIRANGA"
CARGO_EXEMPLO = {
    "uuid": "9b1d5c2e-7f3a-4e88-a1b2-3c4d5e6f7a8b",
    "nome": "PROF. ENS. FUND. II E MEDIO - PORTUGUES",
    "codigo": 3859,
}
ULTIMA_ESCOLHA_EXEMPLO = "2026-09-20T17:32:10.482140+00:00"


def _contagem(total: int, geral: int, pcd: int, nna: int) -> dict[str, int]:
    """Monta uma contagem por lista para os exemplos."""
    return {"total": total, "geral": geral, "pcd": pcd, "nna": nna}


def _dres(butanta: tuple[int, int], ipiranga: tuple[int, int]) -> list[Any]:
    """Monta as escolhas e vagas das duas DREs dos exemplos."""
    return [
        {"nome": DRE_BUTANTA, "escolhas": butanta[0], "vagas": butanta[1]},
        {"nome": DRE_IPIRANGA, "escolhas": ipiranga[0], "vagas": ipiranga[1]},
    ]


def _dres_do_concurso(
    butanta: tuple[int, int], ipiranga: tuple[int, int]
) -> dict[str, Any]:
    """Monta o detalhe por DRE e cargo do concurso dos exemplos."""
    cargo = {
        "codigo_cargo": CARGO_EXEMPLO["codigo"],
        "cargo_descricao": CARGO_EXEMPLO["nome"],
    }
    return {
        UUID_CONCURSO_EXEMPLO: [
            {
                "nome": DRE_BUTANTA,
                "escolhas": butanta[0],
                "vagas": butanta[1],
                **cargo,
                "ultima_escolha_em": ULTIMA_ESCOLHA_EXEMPLO,
            },
            {
                "nome": DRE_IPIRANGA,
                "escolhas": ipiranga[0],
                "vagas": ipiranga[1],
                **cargo,
                "ultima_escolha_em": "2026-09-19T14:05:41.117302+00:00",
            },
        ]
    }


def _autorizacoes(total: int, data: str) -> dict[str, Any]:
    """Monta as autorizações publicadas de um recorte dos exemplos."""
    return {
        "autorizacoes-publicadas": total,
        "cargos": [
            {**CARGO_EXEMPLO, "autorizacoes": total, "data_autorizacao": data}
        ],
    }


HABILITADOS_DO_CONCURSO = _contagem(1200, 1000, 80, 120)

FILTRO_2025 = {"ano": 2025, "processo_uuids": [UUID_PROCESSO_EXEMPLO]}
FILTRO_2026 = {
    "ano": 2026,
    "processo_uuids": [
        "2d9f4c1e-7b6a-4e3d-8c2b-1a0f9e8d7c6b",
        "8e7d6c5b-4a39-4281-9706-f5e4d3c2b1a0",
    ],
}

CANDIDATOS_2025 = {
    "habilitados": _contagem(300, 250, 20, 30),
    "convocados": _contagem(280, 235, 18, 27),
    "nao-convocados": _contagem(920, 765, 62, 93),
}
CANDIDATOS_2026 = {
    "habilitados": _contagem(400, 330, 28, 42),
    "convocados": _contagem(350, 290, 24, 36),
    "nao-convocados": _contagem(850, 710, 56, 84),
}

ESCOLHAS_2025 = {
    "escolha": _contagem(200, 170, 12, 18),
    "nao-escolha": _contagem(40, 34, 2, 4),
    "reconvocacao": _contagem(20, 16, 2, 2),
    "dres": _dres((120, 150), (80, 90)),
}
ESCOLHAS_2026 = {
    "escolha": _contagem(240, 200, 16, 24),
    "nao-escolha": _contagem(50, 42, 3, 5),
    "reconvocacao": _contagem(30, 24, 3, 3),
    "dres": _dres((150, 160), (90, 100)),
}

PENDENTES_2025 = _contagem(20, 15, 2, 3)
PENDENTES_2026 = _contagem(30, 24, 2, 4)

EXEMPLO_UM_ANO = {
    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
    "filtros": [FILTRO_2025, FILTRO_2026],
    "candidatos": {
        "habilitados": HABILITADOS_DO_CONCURSO,
        "2026": CANDIDATOS_2026,
    },
    "escolhas": {
        "concurso_uuid": UUID_CONCURSO_EXEMPLO,
        "filtros": [FILTRO_2026],
        "2026": ESCOLHAS_2026,
        "dres_concursos": _dres_do_concurso((150, 160), (90, 100)),
        "ultima_escolha_em": ULTIMA_ESCOLHA_EXEMPLO,
    },
    "concurso": {"2026": _autorizacoes(400, "2026-03-01")},
    "pendentes": {"2026": PENDENTES_2026},
}

EXEMPLO_DOIS_ANOS = {
    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
    "filtros": [FILTRO_2025, FILTRO_2026],
    "candidatos": {
        "habilitados": HABILITADOS_DO_CONCURSO,
        "2025": CANDIDATOS_2025,
        "2026": CANDIDATOS_2026,
    },
    "escolhas": {
        "concurso_uuid": UUID_CONCURSO_EXEMPLO,
        "filtros": [FILTRO_2025, FILTRO_2026],
        "2025": ESCOLHAS_2025,
        "2026": ESCOLHAS_2026,
        "dres_concursos": _dres_do_concurso((270, 310), (170, 190)),
        "ultima_escolha_em": ULTIMA_ESCOLHA_EXEMPLO,
    },
    "concurso": {
        "2025": _autorizacoes(300, "2025-02-14"),
        "2026": _autorizacoes(400, "2026-03-01"),
    },
    "pendentes": {"2025": PENDENTES_2025, "2026": PENDENTES_2026},
    "comparativo": {
        "anos": [2025, 2026],
        "indicadores": {
            "convocados": 70,
            "naoConvocados": -70,
            "escolhasRealizadas": 40,
            "reconvocacoes": 10,
            "semEscolha": 10,
            "autorizacoes": 100,
        },
        "dres": {
            "BUTANTA": {
                "escolhas": 30,
                "vagas": 10,
                "percentualPreenchimento": 13.8,
            },
            "IPIRANGA": {
                "escolhas": 10,
                "vagas": 10,
                "percentualPreenchimento": 1.1,
            },
        },
    },
}

EXEMPLO_TOTAL = {
    "candidatos": {
        "habilitados": HABILITADOS_DO_CONCURSO,
        "convocados": _contagem(630, 525, 42, 63),
        "nao-convocados": _contagem(570, 475, 38, 57),
    },
    "escolhas": {
        "escolha": _contagem(440, 370, 28, 42),
        "nao-escolha": _contagem(90, 76, 5, 9),
        "reconvocacao": _contagem(50, 40, 5, 5),
        "dres": _dres((270, 310), (170, 190)),
        "dres_concursos": _dres_do_concurso((270, 310), (170, 190)),
        "ultima_escolha_em": ULTIMA_ESCOLHA_EXEMPLO,
    },
    "concurso": _autorizacoes(700, "2026-03-01"),
    "pendentes": _contagem(50, 39, 4, 7),
}

FALHA_DE_COMUNICACAO = (
    "Falha em um dos microsserviços consultados: indisponível, com erro "
    "ou recusando o token repassado."
)

RESPOSTA_FALHA_EXTERNA = resposta(
    ErroDetalheSerializer,
    FALHA_DE_COMUNICACAO,
    {
        "Outro microsserviço com erro": {
            "detail": "Erro ao comunicar com serviço externo."
        }
    },
)

ORIGEM_DOS_BLOCOS = (
    "habilitados e convocados (MS-Candidatos), escolhas e vagas por DRE "
    "(MS-Escolhas) e autorizações publicadas (MS-Concursos). Os três "
    "blocos são repassados como vieram, e este serviço acrescenta "
    "`pendentes`"
)

PENDENTES = (
    "**Pendentes.** Convocados menos os que já têm escolha, não escolha ou "
    "reconvocação registrada, por lista; o resultado nunca fica negativo."
)

FORMATO_INESPERADO = (
    "Resposta de um desses microsserviços que não é JSON responde 502; em "
    "JSON, mas com formato inesperado, pode responder 500."
)

OPERACOES_EXTRACAO_DADOS = {
    "list": extend_schema(
        operation_id="extrair_dados_por_concurso",
        summary="Extrair indicadores de um concurso por ano",
        description=(
            "Reúne os indicadores de um concurso em um ou dois anos: "
            f"{ORIGEM_DOS_BLOCOS} e, com dois anos, `comparativo`.\n\n"
            "**Como os anos são resolvidos.** O serviço busca os processos "
            "de convocação do concurso e os agrupa pelo ano da data de "
            "convocação. `filtros` lista todos os anos encontrados, "
            "inclusive os que não foram pedidos; processo sem data de "
            "convocação é ignorado. Se o concurso não tem processo, ou se "
            "um ano pedido não tem, a resposta é 404.\n\n"
            "**Chaves por ano.** Em `candidatos`, `escolhas`, `concurso` e "
            "`pendentes`, cada ano pedido é uma chave com quatro dígitos, "
            'por exemplo `"2026"`.\n\n'
            f"{PENDENTES}\n\n"
            "**Comparativo.** Só com dois anos: a diferença de cada "
            "indicador, ano mais recente menos o mais antigo, e a "
            "diferença por DRE.\n\n"
            f"{FORMATO_INESPERADO}"
        ),
        filters=False,
        parameters=[
            OpenApiParameter(name="page", exclude=True),
            OpenApiParameter(
                name="concurso_uuid",
                type=OpenApiTypes.UUID,
                required=True,
                description="UUID do concurso.",
            ),
            OpenApiParameter(
                name="ano",
                type={
                    "type": "array",
                    "items": {
                        "type": "integer",
                        "minimum": 1000,
                        "maximum": 9999,
                    },
                    "minItems": 1,
                    "maxItems": 2,
                },
                required=True,
                explode=False,
                style="form",
                description=(
                    "Um ou dois anos, com quatro dígitos, separados por "
                    "vírgula (`ano=2025,2026`). Com dois anos, a resposta "
                    "traz também o `comparativo`. Se o parâmetro for "
                    "repetido (`ano=2025&ano=2026`), só o último vale."
                ),
            ),
        ],
        responses=respostas(
            {
                200: resposta(
                    ExtracaoDadosSerializer,
                    "Indicadores do concurso nos anos pedidos.",
                    {
                        "Um ano": EXEMPLO_UM_ANO,
                        "Dois anos, com comparativo": EXEMPLO_DOIS_ANOS,
                    },
                ),
                400: resposta(
                    ErrosValidacaoSerializer,
                    "Parâmetro ausente ou com valor inválido.",
                    {
                        "Parâmetros ausentes": {
                            "concurso_uuid": ["Este campo é obrigatório."],
                            "ano": ["Este campo é obrigatório."],
                        },
                        "UUID malformado": {
                            "concurso_uuid": ["Must be a valid UUID."]
                        },
                        "Ano com menos de quatro dígitos": {
                            "ano": {
                                "0": [
                                    "Certifque-se de que este valor seja "
                                    "maior ou igual a 1000."
                                ]
                            }
                        },
                        "Mais de dois anos": {
                            "ano": [
                                "Ensure this field has no more than 2 "
                                "elements."
                            ]
                        },
                    },
                ),
                404: resposta(
                    ErroDetalheSerializer,
                    (
                        "Concurso sem processo de convocação, ou ano pedido "
                        "sem processo."
                    ),
                    {
                        "Concurso sem processo": {
                            "detail": (
                                "Nenhum processo de convocação encontrado "
                                "para o concurso informado."
                            )
                        },
                        "Ano sem processo": {
                            "detail": (
                                "Nenhum processo de convocação encontrado "
                                "para o(s) ano(s) 2024."
                            )
                        },
                    },
                ),
                502: RESPOSTA_FALHA_EXTERNA,
            }
        ),
    ),
    "total": extend_schema(
        operation_id="extrair_dados_totais",
        summary="Extrair indicadores de todos os concursos",
        description=(
            "Reúne, para todos os concursos e anos somados, "
            f"{ORIGEM_DOS_BLOCOS}.\n\n"
            "Não aceita parâmetros: os que forem enviados são ignorados. "
            "A resposta não tem chaves por ano nem `comparativo`.\n\n"
            f"{PENDENTES}\n\n"
            f"{FORMATO_INESPERADO}"
        ),
        responses=respostas(
            {
                200: resposta(
                    ExtracaoDadosTotalSerializer,
                    "Indicadores de todos os concursos.",
                    {"Todos os concursos": EXEMPLO_TOTAL},
                ),
                502: RESPOSTA_FALHA_EXTERNA,
            }
        ),
    ),
}
