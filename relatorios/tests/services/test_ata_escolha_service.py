from unittest.mock import Mock

import pytest
from requests import RequestException

from relatorios.services.ata_escolha_service import (
    AtaEscolhaService,
    CargoObrigatorioError,
)


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


@pytest.fixture
def service():
    """Fixture para criar serviço com mocks."""
    svc = AtaEscolhaService(
        candidatos_base_url="http://candidatos",
        processo_base_url="http://processos",
        agendas_base_url="http://agendas",
        escolhas_base_url="http://escolhas",
        timeout_seconds=1,
    )
    svc.candidatos_service = Mock()
    svc.processo_service = Mock()
    svc.agendas_service = Mock()
    svc.escolhas_service = Mock()
    return svc


@pytest.fixture
def agenda_basica():
    """Helper para criar agenda básica."""
    return {
        "cargo_nome": "Professor",
        "cargo_codigo": "123",
        "candidatos_uuids": [],
        "hora_convocacao_inicio": "09:00",
        "hora_convocacao_fim": "10:00",
    }


@pytest.fixture
def candidato_basico():
    """Helper para criar candidato básico."""
    return {
        "uuid": "a",
        "categoria_efetiva": "GERAL",
        "classificacao": 1,
        "ranking_escolha": 1,
        "candidato": {"nome": "Candidato A"},
    }


@pytest.mark.parametrize(
    "classificacoes,esperado",
    [
        ([1, 2, 3, 6, 7], [4, 5]),
        ([None, 2, 2, 5], [3, 4]),
        ([], []),
        ([1], []),
        ([1, 2, 3], []),
        ([5, 1, 3], [2, 4]),
    ],
)
def test_identificar_lacunas(service, classificacoes, esperado):
    """Testa identificação de lacunas em classificações."""
    assert service._identificar_lacunas(classificacoes) == esperado


def test_separar_por_tipo(service):
    """Testa separação de candidatos por tipo (PCD, GERAL, NNA)."""
    candidatos = [
        {"categoria_efetiva": "GERAL", "uuid": "g1"},
        {"categoria_efetiva": "NNA", "uuid": "n1"},
        {"categoria_efetiva": "PCD", "uuid": "p1"},
        {"categoria_efetiva": "PCD", "uuid": "p2"},
        {"uuid": "outro"},
    ]
    separados = service._separar_por_tipo(candidatos)
    assert separados == {
        "geral": [{"categoria_efetiva": "GERAL", "uuid": "g1"}],
        "nna": [{"categoria_efetiva": "NNA", "uuid": "n1"}],
        "pcd": [
            {"categoria_efetiva": "PCD", "uuid": "p1"},
            {"categoria_efetiva": "PCD", "uuid": "p2"},
        ],
    }


@pytest.mark.parametrize(
    "candidatos,campo,esperado",
    [
        (
            [
                {"classificacao": 1},
                {"classificacao": None},
                {},
                {"classificacao": 5},
            ],
            "classificacao",
            [1, None, None, 5],
        ),
        (
            [{"classificacao_pcd": 2}, {"classificacao_pcd": None}],
            "classificacao_pcd",
            [2, None],
        ),
    ],
)
def test_extrair_classificacoes(service, candidatos, campo, esperado):
    """Testa extração de classificações de candidatos."""
    assert service._extrair_classificacoes(candidatos, campo) == esperado


def test_buscar_candidatos_faltantes_sucesso(service):
    """Testa busca de candidatos faltantes com sucesso."""
    service.candidatos_service.buscar_habilitados_por_processos_e_classificacoes.side_effect = [  # noqa: E501
        _Resp(
            [
                {"uuid": "gX", "classificacao": 4},
                {"uuid": "gY", "classificacao": 5},
            ]
        ),
        _Resp([{"uuid": "nX", "classificacao_nna": 3}]),
    ]
    service.candidatos_service.buscar_habilitados.side_effect = [
        _Resp(
            [
                {"uuid": "p1", "classificacao_pcd": 2},
                {"uuid": "z", "classificacao_pcd": None},
            ]
        ),
        _Resp([{"uuid": "p2", "classificacao_pcd": 99}]),
    ]

    res = service._buscar_candidatos_faltantes(
        outros_processos_uuid=["proc-1", "proc-2"],
        lacunas_geral=[4, 5],
        lacunas_nna=[3],
        lacunas_pcd=[2],
        codigo_cargo="123",
        ordering="ranking_escolha",
    )

    assert [c["uuid"] for c in res["geral"]] == ["gX", "gY"]
    assert [c["uuid"] for c in res["nna"]] == ["nX"]
    assert [c["uuid"] for c in res["pcd"]] == ["p1"]
    assert all("status_especial" in c for c in res["nna"] + res["pcd"])
    assert res["geral"][0]["status_especial"] in [
        "JÁ CONVOCADO - LEI 13.398/02",
        "JÁ CONVOCADO - LEI 15.939/13",
        "",
    ]


@pytest.mark.parametrize(
    "outros_processos,esperado",
    [
        ([], {"geral": [], "nna": [], "pcd": []}),
    ],
)
def test_buscar_candidatos_faltantes_sem_outros_processos(
    service, outros_processos, esperado
):
    """Testa busca de candidatos faltantes quando não há outros processos."""
    res = service._buscar_candidatos_faltantes(
        outros_processos_uuid=outros_processos,
        lacunas_geral=[1, 2],
        lacunas_nna=[],
        lacunas_pcd=[],
    )
    assert res == esperado


def test_buscar_candidatos_faltantes_request_exception(service):
    """Testa tratamento de exceção ao buscar candidatos faltantes."""
    service.candidatos_service.buscar_habilitados_por_processos_e_classificacoes.side_effect = RequestException(  # noqa: E501
        "err"
    )
    res = service._buscar_candidatos_faltantes(
        outros_processos_uuid=["x"],
        lacunas_geral=[1],
        lacunas_nna=[],
        lacunas_pcd=[],
    )
    assert res == {"geral": [], "nna": [], "pcd": []}


@pytest.mark.parametrize(
    "candidato_uuids,escolhas_data,esperado_len,esperado_uuids",
    [
        (
            ["uuid1", "uuid2", "uuid3"],
            [
                {
                    "candidato_uuid": "uuid1",
                    "situacao": "escolha",
                    "tipo_vaga": "precaria",
                },
                {
                    "candidato_uuid": "uuid2",
                    "situacao": "escolha",
                    "tipo_vaga": "definitiva",
                },
            ],
            2,
            ["uuid1", "uuid2"],
        ),
        ([], [], 0, []),
    ],
)
def test_buscar_escolhas_por_candidatos(
    service, candidato_uuids, escolhas_data, esperado_len, esperado_uuids
):
    """Testa busca de escolhas por lista de candidatos."""
    service.escolhas_service.buscar_escolhas_por_candidatos.return_value = (
        escolhas_data
    )
    escolhas_map = service._buscar_escolhas_por_candidatos(candidato_uuids)
    assert len(escolhas_map) == esperado_len
    assert all(uuid in escolhas_map for uuid in esperado_uuids)
    if esperado_uuids:
        assert escolhas_map[esperado_uuids[0]]["situacao"] == "escolha"
    if not candidato_uuids:
        service.escolhas_service.buscar_escolhas_por_candidatos.assert_not_called()


def test_buscar_escolhas_por_candidatos_request_exception(service):
    """Testa tratamento de exceção ao buscar escolhas."""
    service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = (
        RequestException("err")
    )
    assert service._buscar_escolhas_por_candidatos(["uuid1"]) == {}


@pytest.mark.parametrize(
    "escolha,esperado",
    [
        (
            {
                "tipo_vaga": "precaria",
                "vaga_escola": {
                    "escola": {
                        "codigo_eol": "12345",
                        "nome_oficial": "Escola Teste",
                        "tipo_ue": "EMEF",
                        "dre": {
                            "sigla": "DRE-TEST",
                            "nome": "Diretoria Regional de Teste",
                        },
                    }
                },
            },
            {
                "codigo_eol": "12345",
                "dre_codigo": "DRE-TEST",
                "dre_nome": "Diretoria Regional de Teste",
                "tipo_unidade": "EMEF",
                "nome_escola": "Escola Teste",
                "tipo_vaga": "P",
            },
        ),
        (
            {
                "tipo_vaga": "definitiva",
                "vaga_escola": {
                    "escola": {
                        "codigo_eol": "67890",
                        "nome_oficial": "Escola Definitiva",
                        "tipo_unidade": "EMEI",
                        "dre": {"sigla": "DRE-DEF", "nome": "DRE Definitiva"},
                    }
                },
            },
            {
                "codigo_eol": "67890",
                "dre_codigo": "DRE-DEF",
                "dre_nome": "DRE Definitiva",
                "tipo_unidade": "EMEI",
                "nome_escola": "Escola Definitiva",
                "tipo_vaga": "D",
            },
        ),
        (
            {"tipo_vaga": "precaria", "vaga_escola": {}},
            {
                "codigo_eol": "",
                "dre_codigo": "",
                "dre_nome": "",
                "tipo_unidade": "",
                "nome_escola": "",
                "tipo_vaga": "P",
            },
        ),
    ],
)
def test_extrair_dados_escola_escolhida(service, escolha, esperado):
    """Testa extração de dados da escola escolhida."""
    dados = service._extrair_dados_escola_escolhida(escolha)
    assert dados == esperado


def _setup_processamento_basico(
    service, agendas, candidatos, escolhas=None, processo_data=None
):
    """Helper para configurar mocks básicos de processamento."""
    service.agendas_service.buscar_agendas.return_value = _Resp(agendas)
    service.candidatos_service.buscar_por_uuids.return_value = _Resp(
        {"results": candidatos}
    )
    service.candidatos_service.buscar_reclassificados_por_concurso.return_value = _Resp(  # noqa: E501
        {}
    )
    service.candidatos_service.buscar_eliminados_por_concurso.return_value = (
        _Resp({})
    )
    service.escolhas_service.buscar_escolhas_por_candidatos.return_value = (
        escolhas or []
    )
    if processo_data:
        service.processo_service.buscar_processo_convocacao.return_value = (
            _Resp(processo_data)
        )
        service.processo_service.separar_processos_por_principal.return_value = (  # noqa: E501
            "p_main",
            ["p2"],
        )
    else:
        service.processo_service.buscar_processo_convocacao.return_value = (
            _Resp({"concurso_uuid": None})
        )


def test_processar_ata_escolha_fluxo_basico(
    service, agenda_basica, candidato_basico
):
    """Testa processamento básico de ata de escolha."""
    agendas = [
        {**agenda_basica, "candidatos_uuids": ["a"]},
        {
            **agenda_basica,
            "candidatos_uuids": ["b", "c"],
            "hora_convocacao_inicio": "10:00",
            "hora_convocacao_fim": "11:00",
        },
    ]
    candidatos = [
        {
            **candidato_basico,
            "uuid": "a",
            "candidato": {
                "nome": "Candidato A",
                "rg": "123456",
                "cpf": "11111111111",
                "registro_funcional": "RF001",
            },
        },
        {
            **candidato_basico,
            "uuid": "b",
            "classificacao": 2,
            "ranking_escolha": 2,
            "candidato": {
                "nome": "Candidato B",
                "rg": "234567",
                "cpf": "22222222222",
                "registro_funcional": "RF002",
            },
        },
        {
            **candidato_basico,
            "uuid": "c",
            "classificacao": 3,
            "ranking_escolha": 3,
            "candidato": {
                "nome": "Candidato C",
                "rg": "345678",
                "cpf": "33333333333",
                "registro_funcional": "RF003",
            },
        },
    ]
    escolhas = [
        {
            "candidato_uuid": "a",
            "situacao": "escolha",
            "tipo_vaga": "precaria",
            "vaga_escola": {
                "escola": {
                    "codigo_eol": "12345",
                    "nome_oficial": "Escola A",
                    "tipo_ue": "EMEF",
                    "dre": {"sigla": "DRE-A", "nome": "DRE A"},
                }
            },
        }
    ]
    processo_data = {"uuid": "proc-abc", "concurso_uuid": None}
    _setup_processamento_basico(
        service, agendas, candidatos, escolhas, processo_data=processo_data
    )

    resultado = service.processar_ata_escolha(
        processo_uuid="proc-abc", ordering="ranking_escolha"
    )

    assert resultado["processo_uuid"] == "proc-abc"
    assert resultado["total_cargos"] == 1
    cargo = resultado["cargos"][0]
    assert cargo["cargo_nome"] == "Professor"
    assert cargo["cargo_codigo"] == "123"
    assert cargo["numero_sessoes"] == 2

    candidatos_todos = [
        c for sessao in cargo["sessoes"] for c in sessao["candidatos"]
    ]
    candidato_a = next(c for c in candidatos_todos if c["uuid"] == "a")
    assert candidato_a["assinatura"] == "Escolha"
    assert candidato_a["codigo_eol"] == "12345"
    assert (
        next(c for c in candidatos_todos if c["uuid"] == "b")["assinatura"]
        == "Não Escolha"
    )


def test_processar_ata_escolha_com_lacunas_e_faltantes(service, agenda_basica):
    """Testa processamento com lacunas e candidatos faltantes."""
    candidatos = [
        {
            "uuid": "a",
            "categoria_efetiva": "GERAL",
            "classificacao": 1,
            "ranking_escolha": 1,
            "candidato": {"nome": "Candidato A"},
        },
        {
            "uuid": "b",
            "categoria_efetiva": "GERAL",
            "classificacao": 3,
            "ranking_escolha": 2,
            "candidato": {"nome": "Candidato B"},
        },
    ]
    _setup_processamento_basico(
        service,
        [agenda_basica],
        candidatos,
        processo_data={"concurso_uuid": "cu1"},
    )
    service.candidatos_service.buscar_habilitados_por_processos_e_classificacoes.return_value = _Resp(  # noqa: E501
        [
            {
                "uuid": "gx",
                "categoria_efetiva": "GERAL",
                "classificacao": 2,
                "candidato": {"nome": "Faltante GX"},
            }
        ]
    )

    resultado = service.processar_ata_escolha(processo_uuid="proc-123")
    candidatos_todos = [
        c
        for sessao in resultado["cargos"][0]["sessoes"]
        for c in sessao["candidatos"]
    ]

    assert "gx" in [c["uuid"] for c in candidatos_todos]
    assert "status_especial" in next(
        c for c in candidatos_todos if c["uuid"] == "gx"
    )


def test_processar_ata_escolha_multiplos_cargos_sem_cargo_levanta_erro(
    service,
):
    """
    Com múltiplos cargos e sem cargo_codigo deve levantar
    CargoObrigatorioError.
    """
    agendas = [
        {
            "cargo_nome": "Professor",
            "cargo_codigo": "123",
            "candidatos_uuids": ["a"],
            "hora_convocacao_inicio": "09:00",
            "hora_convocacao_fim": "10:00",
        },
        {
            "cargo_nome": "Coordenador",
            "cargo_codigo": "456",
            "candidatos_uuids": ["x"],
            "hora_convocacao_inicio": "11:00",
            "hora_convocacao_fim": "12:00",
        },
    ]
    service.agendas_service.buscar_agendas.return_value = _Resp(
        {"results": agendas}
    )
    with pytest.raises(CargoObrigatorioError) as exc_info:
        service.processar_ata_escolha(processo_uuid="proc-multi")
    assert len(exc_info.value.cargos) == 2
    assert {c["cargo_codigo"] for c in exc_info.value.cargos} == {"123", "456"}


def test_processar_ata_escolha_um_cargo_quando_informa_cargo_codigo(service):
    """
    Com múltiplos cargos, ao informar cargo_codigo retorna apenas esse cargo.
    """
    agendas = [
        {
            "cargo_nome": "Professor",
            "cargo_codigo": "123",
            "candidatos_uuids": ["a"],
            "hora_convocacao_inicio": "09:00",
            "hora_convocacao_fim": "10:00",
        },
        {
            "cargo_nome": "Coordenador",
            "cargo_codigo": "456",
            "candidatos_uuids": ["x"],
            "hora_convocacao_inicio": "11:00",
            "hora_convocacao_fim": "12:00",
        },
    ]
    service.agendas_service.buscar_agendas.return_value = _Resp(
        {"results": agendas}
    )
    service.processo_service.buscar_processo_convocacao.return_value = _Resp(
        {"uuid": "proc-multi", "concurso_uuid": None}
    )
    service.candidatos_service.buscar_por_uuids.return_value = _Resp(
        {
            "results": [
                {
                    "uuid": "a",
                    "categoria_efetiva": "GERAL",
                    "classificacao": 1,
                    "ranking_escolha": 1,
                    "candidato": {"nome": "Candidato A"},
                }
            ]
        }
    )
    service.candidatos_service.buscar_reclassificados_por_concurso.return_value = _Resp(  # noqa: E501
        {}
    )
    service.candidatos_service.buscar_eliminados_por_concurso.return_value = (
        _Resp({})
    )
    service.escolhas_service.buscar_escolhas_por_candidatos.return_value = []

    resultado = service.processar_ata_escolha(
        processo_uuid="proc-multi", cargo_codigo="123"
    )

    assert resultado["total_cargos"] == 1
    assert resultado["cargos"][0]["cargo_codigo"] == "123"
    assert resultado["cargos"][0]["cargo_nome"] == "Professor"


def test_processar_ata_escolha_ordenacao_pcd_primeiro(service, agenda_basica):
    """Testa que PCD aparece primeiro na ordenação."""
    candidatos = [
        {
            "uuid": "geral1",
            "categoria_efetiva": "GERAL",
            "classificacao": 1,
            "ranking_escolha": 1,
            "candidato": {"nome": "Geral 1"},
        },
        {
            "uuid": "pcd1",
            "categoria_efetiva": "PCD",
            "classificacao_pcd": 1,
            "ranking_escolha": 5,
            "candidato": {"nome": "PCD 1"},
        },
        {
            "uuid": "nna1",
            "categoria_efetiva": "NNA",
            "classificacao_nna": 1,
            "ranking_escolha": 2,
            "candidato": {"nome": "NNA 1"},
        },
    ]
    _setup_processamento_basico(service, [agenda_basica], candidatos)

    resultado = service.processar_ata_escolha(processo_uuid="proc-pcd")
    candidatos_todos = [
        c
        for sessao in resultado["cargos"][0]["sessoes"]
        for c in sessao["candidatos"]
    ]

    assert candidatos_todos[0]["categoria_efetiva"] == "PCD"


def test_processar_ata_escolha_ordem_escolha(service, agenda_basica):
    """Testa atribuição de ordem_escolha."""
    candidatos = [
        {
            "uuid": "a",
            "categoria_efetiva": "GERAL",
            "classificacao": 1,
            "ranking_escolha": 1,
            "candidato": {"nome": "Candidato A"},
        },
        {
            "uuid": "b",
            "categoria_efetiva": "GERAL",
            "classificacao": 2,
            "ranking_escolha": 2,
            "candidato": {"nome": "Candidato B"},
        },
    ]
    _setup_processamento_basico(service, [agenda_basica], candidatos)

    resultado = service.processar_ata_escolha(processo_uuid="proc-ordem")
    candidatos_todos = [
        c
        for sessao in resultado["cargos"][0]["sessoes"]
        for c in sessao["candidatos"]
    ]

    for i, candidato in enumerate(candidatos_todos, start=1):
        if not candidato.get("status_especial"):
            assert candidato.get("ordem_escolha") == i


def test_processar_ata_escolha_ordem_escolha_com_status_especial(
    service, agenda_basica
):
    """Testa que candidatos com status_especial não recebem ordem_escolha."""
    candidatos = [
        {
            "uuid": "a",
            "categoria_efetiva": "GERAL",
            "classificacao": 1,
            "ranking_escolha": 1,
            "candidato": {"nome": "Candidato A"},
        },
        {
            "uuid": "nna1",
            "categoria_efetiva": "NNA",
            "classificacao_nna": 1,
            "ranking_escolha": 2,
            "candidato": {"nome": "NNA 1"},
        },
        {
            "uuid": "nna3",
            "categoria_efetiva": "NNA",
            "classificacao_nna": 3,
            "ranking_escolha": 3,
            "candidato": {"nome": "NNA 3"},
        },
    ]
    _setup_processamento_basico(
        service,
        [agenda_basica],
        candidatos,
        processo_data={"concurso_uuid": "cu1"},
    )
    service.candidatos_service.buscar_habilitados_por_processos_e_classificacoes.side_effect = (  # noqa: E501
        lambda **kwargs: (
            _Resp(
                [
                    {
                        "uuid": "faltante_nna",
                        "categoria_efetiva": "NNA",
                        "classificacao_nna": 2,
                        "classificacao": 99,
                        "candidato": {"nome": "Faltante NNA"},
                    }
                ]
            )
            if "classificacao_nna" in kwargs
            else _Resp([])
        )
    )

    resultado = service.processar_ata_escolha(processo_uuid="proc-status")
    candidatos_todos = [
        c
        for sessao in resultado["cargos"][0]["sessoes"]
        for c in sessao["candidatos"]
    ]

    candidato_faltante = next(
        c for c in candidatos_todos if c["uuid"] == "faltante_nna"
    )
    assert candidato_faltante.get("ordem_escolha") is None
    assert (
        candidato_faltante.get("status_especial")
        == "CANDIDATOS JÁ CLASSIFICADO."
    )
    assert (
        next(c for c in candidatos_todos if c["uuid"] == "a").get(
            "ordem_escolha"
        )
        is not None
    )


def test_processar_ata_escolha_request_exception(service):
    """Testa tratamento de exceção RequestException."""
    service.agendas_service.buscar_agendas.side_effect = RequestException(
        "falhou"
    )
    with pytest.raises(RequestException):
        service.processar_ata_escolha("proc-err")


@pytest.mark.parametrize(
    "agendas_payload,candidatos_payload",
    [
        (
            {
                "results": [
                    {
                        "cargo_nome": "Professor",
                        "cargo_codigo": "123",
                        "candidatos_uuids": [],
                        "hora_convocacao_inicio": "09:00",
                        "hora_convocacao_fim": "10:00",
                    }
                ]
            },
            {
                "results": [
                    {
                        "uuid": "a",
                        "categoria_efetiva": "GERAL",
                        "classificacao": 1,
                        "ranking_escolha": 1,
                        "candidato": {"nome": "Candidato A"},
                    }
                ]
            },
        ),
        (
            [
                {
                    "cargo_nome": "Professor",
                    "cargo_codigo": "123",
                    "candidatos_uuids": [],
                    "hora_convocacao_inicio": "09:00",
                    "hora_convocacao_fim": "10:00",
                }
            ],
            [
                {
                    "uuid": "a",
                    "categoria_efetiva": "GERAL",
                    "classificacao": 1,
                    "ranking_escolha": 1,
                    "candidato": {"nome": "Candidato A"},
                }
            ],
        ),
    ],
)
def test_processar_ata_escolha_formatos_resposta(
    service, agendas_payload, candidatos_payload
):
    """Testa processamento com diferentes formatos de resposta (dict/list)."""
    candidatos_list = (
        candidatos_payload.get("results", [])
        if isinstance(candidatos_payload, dict)
        else candidatos_payload
    )
    service.agendas_service.buscar_agendas.return_value = _Resp(
        agendas_payload
    )
    service.candidatos_service.buscar_por_uuids.return_value = _Resp(
        {"results": candidatos_list}
    )
    service.candidatos_service.buscar_reclassificados_por_concurso.return_value = _Resp(  # noqa: E501
        {}
    )
    service.candidatos_service.buscar_eliminados_por_concurso.return_value = (
        _Resp({})
    )
    service.processo_service.buscar_processo_convocacao.return_value = _Resp(
        {"concurso_uuid": None}
    )
    service.escolhas_service.buscar_escolhas_por_candidatos.return_value = []

    resultado = service.processar_ata_escolha(processo_uuid="proc-dict")

    assert resultado["total_cargos"] == 1
    assert len(resultado["cargos"]) == 1


@pytest.mark.parametrize(
    "hora_inicio,hora_fim,esperado",
    [
        ("09:00", "10:00", "09:00 às 10:00"),
        ("", "", "Não informado"),
    ],
)
def test_processar_ata_escolha_horario_formatado(
    service, hora_inicio, hora_fim, esperado
):
    """Testa formatação de horário nas sessões."""
    agenda = {
        "cargo_nome": "Professor",
        "cargo_codigo": "123",
        "candidatos_uuids": [],
        "hora_convocacao_inicio": hora_inicio,
        "hora_convocacao_fim": hora_fim,
    }
    candidato = {
        "uuid": "a",
        "categoria_efetiva": "GERAL",
        "classificacao": 1,
        "ranking_escolha": 1,
        "candidato": {"nome": "Candidato A"},
    }
    _setup_processamento_basico(service, [agenda], [candidato])

    resultado = service.processar_ata_escolha(processo_uuid="proc-horario")
    assert (
        resultado["cargos"][0]["sessoes"][0]["horario_formatado"] == esperado
    )
