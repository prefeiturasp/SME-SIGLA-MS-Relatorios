"""Módulo tests/services/test_lauda_convocacao_service."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import pytest
from requests import RequestException

from relatorios.services.lauda_convocacao_service import LaudaConvocacaoService


class _Resp:
    """Representa Resp."""

    def __init__(self, payload: Any) -> None:
        """Inicializa a instância com os parâmetros informados."""
        self._payload = payload

    def json(self) -> Any:
        """Json."""
        return self._payload


def _make_service_with_mocks() -> Any:
    """Make service with mocks."""
    svc = LaudaConvocacaoService(
        candidatos_base_url="http://candidatos",
        processo_base_url="http://processos",
        agendas_base_url="http://agendas",
        timeout_seconds=1,
    )
    svc.candidatos_service = Mock()
    svc.processo_service = Mock()
    svc.agendas_service = Mock()
    svc.escolhas_service = Mock()
    svc.escolhas_service.buscar_escolhas_por_candidatos.return_value = []
    return svc


def test_identificar_lacunas() -> None:
    """Verifica identificar lacunas."""
    svc = _make_service_with_mocks()
    assert svc._identificar_lacunas([1, 2, 3, 6, 7]) == [4, 5]
    assert svc._identificar_lacunas([None, 2, 2, 5]) == [3, 4]
    assert svc._identificar_lacunas([]) == []


def test_separar_por_tipo() -> None:
    """Verifica separar por tipo."""
    svc = _make_service_with_mocks()
    candidatos = [
        {"categoria_efetiva": "GERAL", "uuid": "g1"},
        {"categoria_efetiva": "NNA", "uuid": "n1"},
        {"categoria_efetiva": "PCD", "uuid": "p1"},
        {"uuid": "outro"},
    ]
    separados = svc._separar_por_tipo(candidatos)
    assert len(separados["geral"]) == 1
    assert len(separados["nna"]) == 1
    assert len(separados["pcd"]) == 1


def test_extrair_classificacoes() -> None:
    """Verifica extrair classificacoes."""
    svc = _make_service_with_mocks()
    candidatos = [{"classificacao": 1}, {"classificacao": None}, {}]
    assert svc._extrair_classificacoes(candidatos, "classificacao") == [
        1,
        None,
        None,
    ]


def test_buscar_candidatos_faltantes_sucesso() -> None:
    """Verifica buscar candidatos faltantes sucesso."""
    svc = _make_service_with_mocks()
    outros = ["proc-1", "proc-2"]
    lac_geral = [4, 5]
    lac_nna = [3]
    lac_pcd = [2]
    svc.candidatos_service.buscar_habilitados_por_processos_e_classificacoes.side_effect = [  # noqa: E501
        _Resp(
            [
                {"uuid": "gX", "classificacao": 4},
                {"uuid": "gY", "classificacao": 5},
            ]
        ),
        _Resp([{"uuid": "nX", "classificacao_nna": 3}]),
    ]
    svc.candidatos_service.buscar_habilitados.side_effect = [
        _Resp(
            [
                {"uuid": "p1", "classificacao_pcd": 2},
                {"uuid": "z", "classificacao_pcd": None},
            ]
        ),
        _Resp([{"uuid": "p2", "classificacao_pcd": 99}]),
    ]
    res = svc._buscar_candidatos_faltantes(
        outros_processos_uuid=outros,
        lacunas_geral=lac_geral,
        lacunas_nna=lac_nna,
        lacunas_pcd=lac_pcd,
        codigo_cargo="123",
        ordering="ranking_escolha",
    )
    assert [c["uuid"] for c in res["geral"]] == ["gX", "gY"]
    assert [c["uuid"] for c in res["nna"]] == ["nX"]
    assert [c["uuid"] for c in res["pcd"]] == ["p1"]
    assert all("status_especial" in c for c in res["nna"])
    assert all("status_especial" in c for c in res["pcd"])


def test_buscar_candidatos_faltantes_request_exception() -> None:
    """Verifica buscar candidatos faltantes request exception."""
    svc = _make_service_with_mocks()
    svc.candidatos_service.buscar_habilitados_por_processos_e_classificacoes.side_effect = RequestException(  # noqa: E501
        "err"
    )
    res = svc._buscar_candidatos_faltantes(
        outros_processos_uuid=["x"],
        lacunas_geral=[1],
        lacunas_nna=[],
        lacunas_pcd=[],
    )
    assert res == {"geral": [], "nna": [], "pcd": []}


def test_processar_lauda_convocacao_fluxo_basico() -> None:
    """Verifica processar lauda convocacao fluxo basico."""
    svc = _make_service_with_mocks()
    processo_uuid = "proc-abc"
    agendas_payload = [
        {
            "cargo_nome": "Professor",
            "cargo_codigo": "123",
            "candidatos_uuids": ["a"],
            "hora_convocacao_inicio": "09:00",
            "hora_convocacao_fim": "10:00",
        },
        {
            "cargo_nome": "Professor",
            "cargo_codigo": "123",
            "candidatos_uuids": ["b", "c"],
            "hora_convocacao_inicio": "10:00",
            "hora_convocacao_fim": "11:00",
        },
    ]
    svc.agendas_service.buscar_agendas.return_value = _Resp(agendas_payload)
    candidatos_payload = [
        {
            "uuid": "a",
            "categoria_efetiva": "GERAL",
            "classificacao": 1,
            "ranking_escolha": 1,
        },
        {
            "uuid": "b",
            "categoria_efetiva": "GERAL",
            "classificacao": 2,
            "ranking_escolha": 2,
        },
        {
            "uuid": "c",
            "categoria_efetiva": "GERAL",
            "classificacao": 3,
            "ranking_escolha": 3,
        },
    ]
    svc.candidatos_service.buscar_por_uuids.return_value = _Resp(
        {"results": candidatos_payload}
    )
    svc.processo_service.buscar_processo_convocacao.return_value = _Resp(
        {"concurso_uuid": None}
    )
    svc.candidatos_service.buscar_reclassificados_por_concurso.return_value = (
        _Resp({})
    )
    svc.candidatos_service.buscar_eliminados_por_concurso.return_value = _Resp(
        {}
    )
    resultado = svc.processar_lauda_convocacao(
        processo_uuid=processo_uuid, ordering="ranking_escolha"
    )
    assert resultado["processo_uuid"] == processo_uuid
    assert resultado["total_cargos"] == 1
    cargo = resultado["cargos"][0]
    assert cargo["cargo_nome"] == "Professor"
    assert cargo["numero_sessoes"] == 2
    assert len(cargo["sessoes"]) >= 1
    candidatos_s1 = cargo["sessoes"][0]["candidatos"]
    assert all("ordem_escolha" in c for c in candidatos_s1)


def test_processar_lauda_convocacao_request_exception() -> None:
    """Verifica processar lauda convocacao request exception."""
    svc = _make_service_with_mocks()
    svc.agendas_service.buscar_agendas.side_effect = RequestException("falhou")
    with pytest.raises(RequestException):
        svc.processar_lauda_convocacao("proc-err")


def test_processar_lauda_convocacao_dict_results_merges_geral_faltantes() -> (
    None
):
    """Verifica processar lauda convocacao dict results merges geral faltantes."""
    svc = _make_service_with_mocks()
    processo_uuid = "proc-123"
    agendas_payload = [
        {
            "cargo_nome": "Professor",
            "cargo_codigo": "123",
            "candidatos_uuids": ["x"],
            "hora_convocacao_inicio": "09:00",
            "hora_convocacao_fim": "10:00",
        },
        {
            "cargo_nome": "Professor",
            "cargo_codigo": "123",
            "candidatos_uuids": ["y"],
            "hora_convocacao_inicio": "10:00",
            "hora_convocacao_fim": "11:00",
        },
    ]
    svc.agendas_service.buscar_agendas.return_value = _Resp(agendas_payload)
    candidatos_payload = {
        "results": [
            {
                "uuid": "a",
                "categoria_efetiva": "GERAL",
                "classificacao": 1,
                "ranking_escolha": 1,
            },
            {
                "uuid": "b",
                "categoria_efetiva": "GERAL",
                "classificacao": 3,
                "ranking_escolha": 2,
            },
            {
                "uuid": "c",
                "categoria_efetiva": "GERAL",
                "classificacao": 4,
                "ranking_escolha": 3,
            },
        ]
    }
    svc.candidatos_service.buscar_por_uuids.return_value = _Resp(
        candidatos_payload
    )
    svc.candidatos_service.buscar_reclassificados_por_concurso.return_value = (
        _Resp({})
    )
    svc.candidatos_service.buscar_eliminados_por_concurso.return_value = _Resp(
        {}
    )
    svc.processo_service.buscar_processo_convocacao.return_value = _Resp(
        {"concurso_uuid": "cu1"}
    )
    svc.processo_service.separar_processos_por_principal.return_value = (
        "p_main",
        ["p2"],
    )
    svc._buscar_candidatos_faltantes = Mock(
        return_value={
            "geral": [
                {
                    "uuid": "gx",
                    "categoria_efetiva": "GERAL",
                    "classificacao": 3,
                },
                {
                    "uuid": "gy",
                    "categoria_efetiva": "GERAL",
                    "classificacao": 2,
                },
            ],
            "nna": [],
            "pcd": [],
        }
    )
    resultado = svc.processar_lauda_convocacao(processo_uuid=processo_uuid)
    cargo = resultado["cargos"][0]
    s1 = cargo["sessoes"][0]["candidatos"]
    s1_uuids = [c["uuid"] for c in s1]
    assert "a" in s1_uuids and "gy" in s1_uuids
    all_uuids = [c["uuid"] for s in cargo["sessoes"] for c in s["candidatos"]]
    assert all_uuids.index("gy") < all_uuids.index("b")


def test_processar_lauda_convocacao_sorts_and_merges_all_categories() -> None:
    """Verifica processar lauda convocacao sorts and merges all categories."""
    svc = _make_service_with_mocks()
    processo_uuid = "proc-456"
    agendas_payload = [
        {
            "cargo_nome": "Cargo",
            "cargo_codigo": "999",
            "candidatos_uuids": ["a"],
        },
        {
            "cargo_nome": "Cargo",
            "cargo_codigo": "999",
            "candidatos_uuids": ["b", "c"],
        },
    ]
    svc.agendas_service.buscar_agendas.return_value = _Resp(agendas_payload)
    candidatos_payload = {
        "results": [
            {
                "uuid": "a",
                "categoria_efetiva": "GERAL",
                "classificacao": 1,
                "ranking_escolha": 1,
            },
            {
                "uuid": "b",
                "categoria_efetiva": "GERAL",
                "classificacao": 4,
                "ranking_escolha": 2,
            },
            {"uuid": "n1", "categoria_efetiva": "NNA", "classificacao_nna": 1},
            {"uuid": "n2", "categoria_efetiva": "NNA", "classificacao_nna": 3},
            {"uuid": "p1", "categoria_efetiva": "PCD", "classificacao_pcd": 5},
            {"uuid": "p2", "categoria_efetiva": "PCD", "classificacao_pcd": 7},
        ]
    }
    svc.candidatos_service.buscar_por_uuids.return_value = _Resp(
        candidatos_payload
    )
    svc.candidatos_service.buscar_reclassificados_por_concurso.return_value = (
        _Resp({})
    )
    svc.candidatos_service.buscar_eliminados_por_concurso.return_value = _Resp(
        {}
    )
    svc.processo_service.buscar_processo_convocacao.return_value = _Resp(
        {"concurso_uuid": "cu2"}
    )
    svc.processo_service.separar_processos_por_principal.return_value = (
        "p_main",
        ["pX"],
    )
    svc._buscar_candidatos_faltantes = Mock(
        return_value={
            "geral": [
                {
                    "uuid": "g3",
                    "categoria_efetiva": "GERAL",
                    "classificacao": 3,
                },
                {
                    "uuid": "g2",
                    "categoria_efetiva": "GERAL",
                    "classificacao": 2,
                },
            ],
            "nna": [
                {
                    "uuid": "nn3",
                    "categoria_efetiva": "NNA",
                    "classificacao_nna": 3,
                    "classificacao": 8,
                },
                {
                    "uuid": "nn2",
                    "categoria_efetiva": "NNA",
                    "classificacao_nna": 2,
                    "classificacao": 6,
                },
            ],
            "pcd": [
                {
                    "uuid": "pp7",
                    "categoria_efetiva": "PCD",
                    "classificacao_pcd": 7,
                    "classificacao": 9,
                },
                {
                    "uuid": "pp6",
                    "categoria_efetiva": "PCD",
                    "classificacao_pcd": 6,
                    "classificacao": 7,
                },
            ],
        }
    )
    resultado = svc.processar_lauda_convocacao(processo_uuid=processo_uuid)
    cargo = resultado["cargos"][0]
    all_uuids = [c["uuid"] for s in cargo["sessoes"] for c in s["candidatos"]]
    assert all_uuids.index("g2") < all_uuids.index("g3")
    for uid in ("nn2", "nn3", "pp6", "pp7"):
        assert uid in all_uuids
