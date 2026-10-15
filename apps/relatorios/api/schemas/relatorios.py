"""Documentação OpenAPI da geração e do histórico de relatórios."""

from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    PolymorphicProxySerializer,
    extend_schema,
)

from core.openapi import (
    DOCX,
    HTML,
    JSON,
    PARAMETRO_PAGINA,
    PARAMETRO_TAMANHO_PAGINA,
    PDF,
    RESPOSTA_PAGINA_INEXISTENTE,
    TAMANHO_PAGINA_PADRAO,
    UUID_PROCESSO_EXEMPLO,
    XLSX,
    exemplos_requisicao,
    parametro_busca,
    resposta,
    resposta_arquivo,
    resposta_nao_encontrado,
    respostas,
)
from core.serializers import ErroDetalheSerializer, ErrosValidacaoSerializer
from relatorios.models import Relatorio
from relatorios.models.constants import TIPOS_RELATORIOS
from relatorios.serializers import (
    CargoObrigatorioSerializer,
    ErroRelatorioSerializer,
    GeracaoRelatorioSerializer,
    RelatorioPaginadoSerializer,
    RelatorioSerializer,
)

TAG_RELATORIOS = "Relatórios"

RF_EXEMPLO = "1234567"
CARGO_EXEMPLO = "PROF. ENS. FUND. II E MEDIO - PORTUGUES"
URL_VAGAS_EXEMPLO = (
    "http://localhost:8004/api/v1/vagas-escolas/"
    f"?processo_uuid={UUID_PROCESSO_EXEMPLO}"
)

OBSERVACOES_DOS_TIPOS = {
    "RESULTADO_ESCOLHA": "Em DOCX responde sempre 500.",
    "LISTA_CANDIDATOS_SESSAO": (
        "Com `agenda_uuid`, lista só aquela sessão; sem ele, todas as do "
        "processo. Sessões de retardatários ficam fora."
    ),
    "ATA_ESCOLHA": (
        "Se o processo tem agendas de mais de um cargo, exige "
        "`cargo_codigo`. Processo sem agendas responde 500."
    ),
}

TABELA_DE_TIPOS = "\n".join(
    [
        "| `tipo` | Relatório | Observações |",
        "|---|---|---|",
        *(
            f"| `{tipo}` | {nome} | {OBSERVACOES_DOS_TIPOS.get(tipo, '')} |"
            for tipo, nome in TIPOS_RELATORIOS
        ),
    ]
)

RELATORIO_GERADO = (
    "Relatório gerado, no formato pedido. PDF, XLSX e DOCX vêm com "
    "`Content-Disposition: attachment` e o nome do arquivo."
)

TRECHO_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>Relatório de Vagas por Cargo e DRE</title>
  <!-- estilos omitidos neste trecho -->
</head>
<body>
  <div class="container">
    <div class="cabecalho">
      <p>PREFEITURA DO MUNICÍPIO DE SÃO PAULO</p>
      <p>SECRETARIA MUNICIPAL DE EDUCAÇÃO</p>
    </div>
    <div class="conteudo-relatorio">
      <div class="rel-vagas-escolas">
        <h1>Relação de Vagas</h1>
        <div class="cargo-section">
          <div class="cargo-header">
            Cargo: PROF. ENS. FUND. II E MEDIO - PORTUGUES
          </div>
          <div class="dre-section">
            <div class="dre-header">
              DRE - DIRETORIA REGIONAL DE EDUCACAO BUTANTA
            </div>
            <div class="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Tipo de unidade</th>
                    <th>Código EOL</th>
                    <th>Unidade</th>
                    <th style="text-align: center;">Vagas Definitivas</th>
                    <th style="text-align: center;">Vagas Precárias</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td class="tipo-unidade">EMEF</td>
                    <td>094765</td>
                    <td>EMEF PROF. JOAO DA SILVA</td>
                    <td class="numero-vaga vaga-definitiva">2</td>
                    <td class="numero-vaga vaga-precaria">1</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
"""

EXEMPLO_RELATORIO = {
    "id": 1,
    "uuid": "abc3b03c-cf34-4f46-ab61-058a32e8f014",
    "criado_em": "2026-09-20T11:00:02.983363-03:00",
    "atualizado_em": "2026-09-20T11:00:02.983395-03:00",
    "tipo": "SUMULA_NAO_ESCOLHAS",
    "usuario": RF_EXEMPLO,
    "dados": [
        {
            "codigo": "3859",
            "descricao": CARGO_EXEMPLO,
            "candidatos": [
                {
                    "cargo_codigo": "3859",
                    "cargo_descricao": CARGO_EXEMPLO,
                    "classificacao_geral": 152,
                    "classificacao_def": "-",
                    "classificacao_nna": 31,
                    "nome": "MARIA APARECIDA DA SILVA",
                    "cpf": "12345678909",
                }
            ],
        }
    ],
    "processo_uuid": UUID_PROCESSO_EXEMPLO,
    "cabecalho": None,
    "agenda_uuid": None,
    "usou_cabecalho_padrao": False,
    "usou_logotipo": False,
    "texto_final": None,
    "cabecalho_capa_ata": None,
}

EXEMPLO_PAGINA = {
    "links": {"next": None, "previous": None},
    "count": 1,
    "page": 1,
    "page_size": TAMANHO_PAGINA_PADRAO,
    "results": [EXEMPLO_RELATORIO],
}

CAMPOS_OBRIGATORIOS_AUSENTES = {
    "tipo": ["Este campo é obrigatório."],
    "usuario": ["Este campo é obrigatório."],
    "processo_uuid": ["Este campo é obrigatório."],
}
TIPO_INEXISTENTE = {"tipo": ['"XYZ" não é um escolha válido.']}

ERRO_GERACAO = PolymorphicProxySerializer(
    component_name="ErroGeracaoRelatorio",
    serializers=[
        ErrosValidacaoSerializer,
        CargoObrigatorioSerializer,
        ErroRelatorioSerializer,
    ],
    resource_type_field_name=None,
    many=False,
)

PARAMETRO_ID = OpenApiParameter(
    name="id",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.PATH,
    description=(
        "Identificador numérico do registro, o campo `id` das respostas. "
        "O `uuid` não é aceito nesta rota."
    ),
)

PARAMETRO_FORMATO = OpenApiParameter(
    name="formato",
    type=OpenApiTypes.STR,
    enum=["html", "pdf", "xlsx", "xls", "docx", "doc"],
    description=(
        "Formato do arquivo: `pdf`, `xlsx` (ou `xls`) ou `docx` (ou "
        "`doc`). Sem o parâmetro, ou com qualquer outro valor, inclusive "
        "`csv`, o relatório vem em HTML. Maiúsculas e minúsculas não "
        "importam."
    ),
)

PARAMETROS_LISTAGEM = [
    OpenApiParameter(
        name="tipo",
        type=OpenApiTypes.STR,
        enum=[tipo for tipo, _ in TIPOS_RELATORIOS],
        description="Retorna apenas os relatórios do tipo informado.",
    ),
    parametro_busca("Busca por trecho do tipo, por exemplo `LAUDA`."),
    OpenApiParameter(
        name="ordering",
        type=OpenApiTypes.STR,
        enum=["criado_em", "-criado_em"],
        description=(
            "Ordem pela data de geração: `-criado_em`, do mais recente ao "
            "mais antigo (padrão), ou `criado_em`, o inverso."
        ),
    ),
    PARAMETRO_PAGINA,
    PARAMETRO_TAMANHO_PAGINA,
]

RESPOSTA_REGISTRO = resposta(
    RelatorioSerializer,
    "Registro do histórico.",
    {"Súmula de não escolhas": EXEMPLO_RELATORIO},
)

RESPOSTA_NAO_ENCONTRADO = resposta_nao_encontrado(Relatorio)

VALORES_INVALIDOS = {
    "RF longo demais": {
        "usuario": [
            "Certifique-se de que este campo não tenha mais de 20 "
            "caracteres."
        ]
    },
    "UUID de agenda malformado": {"agenda_uuid": ["Must be a valid UUID."]},
}

CARGO_FORA_DO_PROCESSO = {"error": "Cargo '9999' não encontrado no processo."}
RESPOSTA_FORA_DO_FORMATO = {
    "error": "Expecting value: line 1 column 1 (char 0)"
}

ALTERACAO_DO_HISTORICO = (
    "A operação só muda o registro guardado: não gera o relatório de novo "
    "nem altera o arquivo já entregue. Aqui `usuario` aceita até 20 "
    "caracteres e `cabecalho` até 255, limites que a geração não confere."
)

OPERACOES_RELATORIOS = {
    "list": extend_schema(
        operation_id="listar_relatorios",
        summary="Listar o histórico de relatórios gerados",
        description=(
            "Lista os registros gravados a cada relatório gerado, do mais "
            "recente ao mais antigo, com paginação. Cada registro traz o "
            "pedido e, em `dados`, tudo o que foi usado para montar o "
            "relatório, o que pode deixar a resposta grande.\n\n"
            "`page_size` que não é número e `page=last` respondem 500."
        ),
        parameters=PARAMETROS_LISTAGEM,
        responses=respostas(
            {
                200: resposta(
                    RelatorioPaginadoSerializer,
                    "Página do histórico.",
                    {"Lista paginada": EXEMPLO_PAGINA},
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
                404: RESPOSTA_PAGINA_INEXISTENTE,
            }
        ),
    ),
    "create": extend_schema(
        operation_id="gerar_relatorio",
        summary="Gerar relatório",
        description=(
            "Gera o relatório do tipo pedido para um processo de "
            "convocação e responde com o próprio arquivo. Os dados são "
            "consultados nos outros microsserviços na hora da chamada.\n\n"
            "**Formato.** Vem do parâmetro `formato`: HTML, que é o padrão "
            "e o que o frontend pede na prévia, ou PDF, XLSX ou DOCX.\n\n"
            "No Swagger, deixe o tipo de mídia da resposta em `text/html` "
            "e escolha o formato só pelo parâmetro: o serviço responde 406 "
            "quando o cabeçalho `Accept` traz apenas o tipo de um dos "
            "arquivos. O formato também pode ser pedido pelo `Accept`, "
            "desde que o cabeçalho aceite também `*/*`.\n\n"
            "**Tipos.**\n\n"
            f"{TABELA_DE_TIPOS}\n\n"
            "**Histórico.** Cada geração bem-sucedida grava um registro, "
            "listado em `GET /relatorios/`, com o pedido e os dados "
            "usados. Se a gravação falha, o relatório é devolvido mesmo "
            "assim: é o que acontece quando `agenda_uuid` vem vazio ou não "
            "é um UUID.\n\n"
            "**Textos.** Cabeçalhos, texto final e logotipo vêm da "
            "parametrização e da personalização do tipo. O `cabecalho` do "
            "corpo não muda o relatório; ele só fica no histórico.\n\n"
            "**Falhas.** Erro em outro microsserviço, inclusive token "
            "recusado por ele, responde 500 com o texto técnico da "
            "chamada, que traz a URL interna consultada. Resposta de outro "
            "microsserviço que não é JSON responde 400."
        ),
        parameters=[PARAMETRO_FORMATO],
        request={JSON: GeracaoRelatorioSerializer},
        examples=exemplos_requisicao(
            {
                "Lauda de vagas": {
                    "tipo": "LAUDA_VAGAS",
                    "usuario": RF_EXEMPLO,
                    "processo_uuid": UUID_PROCESSO_EXEMPLO,
                },
                "Lista de candidatos de uma sessão": {
                    "tipo": "LISTA_CANDIDATOS_SESSAO",
                    "usuario": RF_EXEMPLO,
                    "processo_uuid": UUID_PROCESSO_EXEMPLO,
                    "agenda_uuid": "b9eb91a4-f68b-429d-a6ed-5218e8f89872",
                },
                "Ata de Escolha de um cargo": {
                    "tipo": "ATA_ESCOLHA",
                    "usuario": RF_EXEMPLO,
                    "processo_uuid": UUID_PROCESSO_EXEMPLO,
                    "cargo_codigo": "3859",
                },
            }
        ),
        responses=respostas(
            {
                (200, HTML): resposta_arquivo(
                    RELATORIO_GERADO,
                    HTML,
                    {"Trecho de uma Lauda de Vagas": TRECHO_HTML},
                ),
                (200, PDF): resposta_arquivo(RELATORIO_GERADO, PDF),
                (200, XLSX): resposta_arquivo(RELATORIO_GERADO, XLSX),
                (200, DOCX): resposta_arquivo(RELATORIO_GERADO, DOCX),
                400: resposta(
                    ERRO_GERACAO,
                    (
                        "Corpo inválido, Ata de Escolha que precisa do "
                        "cargo, cargo que não está no processo ou resposta "
                        "ilegível de outro microsserviço."
                    ),
                    {
                        "Campos obrigatórios ausentes": (
                            CAMPOS_OBRIGATORIOS_AUSENTES
                        ),
                        "Tipo inexistente": TIPO_INEXISTENTE,
                        "UUID de processo malformado": {
                            "processo_uuid": ["Must be a valid UUID."]
                        },
                        "Ata de processo com mais de um cargo": {
                            "error": (
                                "Selecione um cargo para emitir a Ata de "
                                "Escolha."
                            ),
                            "cargos": [
                                {
                                    "cargo_codigo": "3859",
                                    "cargo_nome": CARGO_EXEMPLO,
                                },
                                {
                                    "cargo_codigo": "3860",
                                    "cargo_nome": (
                                        "PROF. ENS. FUND. II E MEDIO - "
                                        "MATEMATICA"
                                    ),
                                },
                            ],
                        },
                        "Cargo que não está no processo": (
                            CARGO_FORA_DO_PROCESSO
                        ),
                        "Outro microsserviço respondeu fora do formato": (
                            RESPOSTA_FORA_DO_FORMATO
                        ),
                    },
                ),
                406: resposta(
                    ErroDetalheSerializer,
                    (
                        "Cabeçalho `Accept` só com o tipo de um dos "
                        "arquivos, sem `*/*`."
                    ),
                    {
                        "Accept só com PDF": {
                            "detail": (
                                "Não foi possível satisfazer a requisição "
                                "do cabeçalho Accept."
                            )
                        }
                    },
                ),
                500: resposta(
                    ErroRelatorioSerializer,
                    (
                        "Falha ao consultar outro microsserviço ou ao "
                        "montar o relatório."
                    ),
                    {
                        "Outro microsserviço com erro": {
                            "error": (
                                "Erro ao gerar relatório: 500 Server "
                                "Error: Internal Server Error for url: "
                                f"{URL_VAGAS_EXEMPLO}"
                            )
                        },
                        "Token recusado por outro microsserviço": {
                            "error": (
                                "Erro ao gerar relatório: 403 Client "
                                "Error: Forbidden for url: "
                                f"{URL_VAGAS_EXEMPLO}"
                            )
                        },
                        "Tipo sem personalização cadastrada": {
                            "error": (
                                "Erro ao gerar relatório: "
                                "ConfiguracaoRelatorio matching query does "
                                "not exist."
                            )
                        },
                        "Resultado de Escolha em DOCX": {
                            "error": (
                                "Erro ao gerar relatório: "
                                "ResultadoEscolha.render_to_docx() got "
                                "multiple values for argument 'filename'"
                            )
                        },
                        "Ata de processo sem agendas": {
                            "error": (
                                "Erro ao gerar relatório: cannot access "
                                "local variable 'candidatos_sep_cargo' "
                                "where it is not associated with a value"
                            )
                        },
                    },
                ),
            }
        ),
    ),
    "retrieve": extend_schema(
        operation_id="detalhar_relatorio",
        summary="Detalhar registro do histórico",
        description=(
            "Devolve um registro do histórico pelo `id` numérico, com o "
            "pedido e os dados usados para montar o relatório."
        ),
        parameters=[PARAMETRO_ID],
        responses=respostas(
            {200: RESPOSTA_REGISTRO, 404: RESPOSTA_NAO_ENCONTRADO}
        ),
    ),
    "update": extend_schema(
        operation_id="atualizar_relatorio",
        summary="Substituir registro do histórico",
        description=(
            "Substitui os dados de um registro do histórico. Exige `tipo`, "
            "`usuario` e `processo_uuid`; o que não é enviado fica como "
            f"está.\n\n{ALTERACAO_DO_HISTORICO}"
        ),
        parameters=[PARAMETRO_ID],
        request={JSON: RelatorioSerializer},
        examples=exemplos_requisicao(
            {
                "Campos obrigatórios": {
                    "tipo": "SUMULA_NAO_ESCOLHAS",
                    "usuario": "7654321",
                    "processo_uuid": UUID_PROCESSO_EXEMPLO,
                }
            }
        ),
        responses=respostas(
            {
                200: RESPOSTA_REGISTRO,
                400: resposta(
                    ErrosValidacaoSerializer,
                    "Campo obrigatório ausente ou campo com valor inválido.",
                    {
                        "Campos obrigatórios ausentes": (
                            CAMPOS_OBRIGATORIOS_AUSENTES
                        ),
                        **VALORES_INVALIDOS,
                    },
                ),
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
    "partial_update": extend_schema(
        operation_id="atualizar_parcial_relatorio",
        summary="Alterar registro do histórico",
        description=(
            "Altera os campos enviados de um registro do histórico.\n\n"
            f"{ALTERACAO_DO_HISTORICO}"
        ),
        parameters=[PARAMETRO_ID],
        request={JSON: RelatorioSerializer},
        examples=exemplos_requisicao(
            {"Corrigir o RF": {"usuario": "7654321"}}
        ),
        responses=respostas(
            {
                200: RESPOSTA_REGISTRO,
                400: resposta(
                    ErrosValidacaoSerializer,
                    "Campo com valor inválido.",
                    {
                        "Tipo inexistente": TIPO_INEXISTENTE,
                        **VALORES_INVALIDOS,
                    },
                ),
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
    "destroy": extend_schema(
        operation_id="excluir_relatorio",
        summary="Excluir registro do histórico",
        description=(
            "Remove um registro do histórico. O arquivo já entregue não é "
            "afetado."
        ),
        parameters=[PARAMETRO_ID],
        responses=respostas(
            {
                204: resposta(None, "Registro excluído."),
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
}
