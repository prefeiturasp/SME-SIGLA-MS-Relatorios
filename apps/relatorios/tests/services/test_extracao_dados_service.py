from unittest.mock import Mock, patch

import pytest
import requests
from rest_framework.exceptions import NotFound

from relatorios.services.extracao_dados_service import ExtracaoDadosService


class _Resp:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"status={self.status_code}")


def _processos_response(processos):
    return _Resp({"results": processos})


@patch("relatorios.services.extracao_dados_service.ConcursoService")
@patch("relatorios.services.extracao_dados_service.EscolhasService")
@patch("relatorios.services.extracao_dados_service.CandidatosService")
@patch("relatorios.services.extracao_dados_service.ProcessoConvocacaoService")
def test_extrair_por_concurso_chama_microservicos_com_filtros(
    mock_processo_cls,
    mock_candidatos_cls,
    mock_escolhas_cls,
    mock_concurso_cls,
):
    concurso_uuid = "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
    mock_processo = Mock()
    mock_processo.buscar_processos_por_concurso.return_value = (
        _processos_response(
            [
                {
                    "uuid": "proc-2026-a",
                    "data_convocacao": "2026-03-15T10:00:00Z",
                },
                {
                    "uuid": "proc-2026-b",
                    "data_convocacao": "2026-06-20T10:00:00Z",
                },
                {
                    "uuid": "proc-2025-a",
                    "data_convocacao": "2025-01-10T10:00:00Z",
                },
            ]
        )
    )
    mock_processo_cls.return_value = mock_processo

    mock_candidatos = Mock()
    mock_candidatos.buscar_extracao_dados.return_value = {
        "habilitados": {"total": 10000, "geral": 8000, "pcd": 1000, "nna": 1000},
        "2026": {
            "convocados": {"total": 150, "geral": 100, "pcd": 30, "nna": 20},
            "nao-convocados": {
                "total": 9850,
                "geral": 7900,
                "pcd": 970,
                "nna": 980,
            },
        },
    }
    mock_candidatos_cls.return_value = mock_candidatos

    mock_escolhas = Mock()
    mock_escolhas.buscar_extracao_dados.return_value = {
        "2026": {
            "escolha": {"total": 100, "geral": 70, "pcd": 20, "nna": 10},
            "nao-escolha": {"total": 20, "geral": 10, "pcd": 5, "nna": 5},
            "reconvocacao": {"total": 10, "geral": 5, "pcd": 3, "nna": 2},
        }
    }
    mock_escolhas_cls.return_value = mock_escolhas

    mock_concurso = Mock()
    mock_concurso.buscar_extracao_dados.return_value = {
        "2026": {"autorizacoes-publicadas": 100}
    }
    mock_concurso_cls.return_value = mock_concurso

    service = ExtracaoDadosService()
    resultado = service.extrair(concurso_uuid=concurso_uuid, anos=[2026])

    assert resultado["concurso_uuid"] == concurso_uuid
    assert resultado["filtros"] == [
        {
            "ano": 2025,
            "processo_uuids": ["proc-2025-a"],
        },
        {
            "ano": 2026,
            "processo_uuids": ["proc-2026-a", "proc-2026-b"],
        },
    ]
    assert resultado["candidatos"]["habilitados"]["total"] == 10000
    assert resultado["escolhas"]["2026"]["escolha"]["total"] == 100
    assert resultado["pendentes"]["2026"] == {
        "total": 20,
        "geral": 15,
        "pcd": 2,
        "nna": 3,
    }
    assert "comparativo" not in resultado
    filtros_esperados = [
        {
            "ano": 2026,
            "processo_uuids": ["proc-2026-a", "proc-2026-b"],
        },
    ]
    mock_candidatos.buscar_extracao_dados.assert_called_once_with(
        concurso_uuid=concurso_uuid,
        filtros=filtros_esperados,
    )
    mock_escolhas.buscar_extracao_dados.assert_called_once_with(
        concurso_uuid=concurso_uuid,
        filtros=filtros_esperados,
    )
    mock_concurso.buscar_extracao_dados.assert_called_once_with(
        concurso_uuid=concurso_uuid,
        anos=[2026],
    )


@patch("relatorios.services.extracao_dados_service.ConcursoService")
@patch("relatorios.services.extracao_dados_service.EscolhasService")
@patch("relatorios.services.extracao_dados_service.CandidatosService")
@patch("relatorios.services.extracao_dados_service.ProcessoConvocacaoService")
def test_extrair_dois_anos_retorna_comparativo(
    mock_processo_cls,
    mock_candidatos_cls,
    mock_escolhas_cls,
    mock_concurso_cls,
):
    concurso_uuid = "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
    mock_processo = Mock()
    mock_processo.buscar_processos_por_concurso.return_value = (
        _processos_response(
            [
                {
                    "uuid": "proc-2026-a",
                    "data_convocacao": "2026-03-15T10:00:00Z",
                },
                {
                    "uuid": "proc-2025-a",
                    "data_convocacao": "2025-01-10T10:00:00Z",
                },
            ]
        )
    )
    mock_processo_cls.return_value = mock_processo

    mock_candidatos = Mock()
    mock_candidatos.buscar_extracao_dados.return_value = {
        "habilitados": {"total": 100, "geral": 80, "pcd": 10, "nna": 10},
        "2025": {
            "convocados": {"total": 80, "geral": 60, "pcd": 10, "nna": 10},
            "nao-convocados": {"total": 20, "geral": 20, "pcd": 0, "nna": 0},
        },
        "2026": {
            "convocados": {"total": 100, "geral": 80, "pcd": 10, "nna": 10},
            "nao-convocados": {"total": 0, "geral": 0, "pcd": 0, "nna": 0},
        },
    }
    mock_candidatos_cls.return_value = mock_candidatos

    mock_escolhas = Mock()
    mock_escolhas.buscar_extracao_dados.return_value = {
        "2025": {
            "escolha": {"total": 50, "geral": 40, "pcd": 5, "nna": 5},
            "reconvocacao": {"total": 10, "geral": 8, "pcd": 1, "nna": 1},
            "nao-escolha": {"total": 5, "geral": 4, "pcd": 1, "nna": 0},
            "dres": [
                {
                    "nome": "Diretoria Regional de Educação Centro",
                    "escolhas": 20,
                    "vagas": 40,
                }
            ],
        },
        "2026": {
            "escolha": {"total": 75, "geral": 60, "pcd": 10, "nna": 5},
            "reconvocacao": {"total": 5, "geral": 4, "pcd": 1, "nna": 0},
            "nao-escolha": {"total": 10, "geral": 8, "pcd": 1, "nna": 1},
            "dres": [
                {
                    "nome": "Diretoria Regional de Educação Centro",
                    "escolhas": 30,
                    "vagas": 40,
                }
            ],
        },
    }
    mock_escolhas_cls.return_value = mock_escolhas

    mock_concurso = Mock()
    mock_concurso.buscar_extracao_dados.return_value = {
        "2025": {"autorizacoes-publicadas": 80},
        "2026": {"autorizacoes-publicadas": 100},
    }
    mock_concurso_cls.return_value = mock_concurso

    service = ExtracaoDadosService()
    resultado = service.extrair(concurso_uuid=concurso_uuid, anos=[2026, 2025])

    comparativo = resultado["comparativo"]
    assert resultado["concurso_uuid"] == concurso_uuid
    assert resultado["filtros"] == [
        {"ano": 2025, "processo_uuids": ["proc-2025-a"]},
        {"ano": 2026, "processo_uuids": ["proc-2026-a"]},
    ]
    assert comparativo["anos"] == [2025, 2026]
    assert comparativo["indicadores"]["convocados"] == 20.0
    assert comparativo["indicadores"]["naoConvocados"] == -20.0
    assert comparativo["indicadores"]["escolhasRealizadas"] == 25.0
    assert comparativo["indicadores"]["reconvocacoes"] == -5.0
    assert comparativo["indicadores"]["semEscolha"] == 5.0
    assert comparativo["indicadores"]["autorizacoes"] == 20.0
    assert comparativo["dres"]["Centro"]["escolhas"] == 10.0
    assert comparativo["dres"]["Centro"]["vagas"] == 0.0
    assert comparativo["dres"]["Centro"]["percentualPreenchimento"] == 25.0

    mock_concurso.buscar_extracao_dados.assert_called_once_with(
        concurso_uuid=concurso_uuid,
        anos=[2025, 2026],
    )


@patch("relatorios.services.extracao_dados_service.ConcursoService")
@patch("relatorios.services.extracao_dados_service.EscolhasService")
@patch("relatorios.services.extracao_dados_service.CandidatosService")
def test_extrair_total_chama_microservicos_sem_parametros(
    mock_candidatos_cls,
    mock_escolhas_cls,
    mock_concurso_cls,
):
    mock_candidatos = Mock()
    mock_candidatos.buscar_extracao_dados.return_value = {
        "habilitados": {
            "total": 50000,
            "geral": 40000,
            "pcd": 5000,
            "nna": 5000,
        },
        "convocados": {"total": 1000, "geral": 800, "pcd": 100, "nna": 100},
        "nao-convocados": {
            "total": 49000,
            "geral": 39200,
            "pcd": 4900,
            "nna": 4900,
        },
    }
    mock_candidatos_cls.return_value = mock_candidatos

    mock_escolhas = Mock()
    mock_escolhas.buscar_extracao_dados.return_value = {
        "escolha": {"total": 600, "geral": 480, "pcd": 60, "nna": 60},
        "nao-escolha": {"total": 200, "geral": 160, "pcd": 20, "nna": 20},
        "reconvocacao": {"total": 100, "geral": 80, "pcd": 10, "nna": 10},
    }
    mock_escolhas_cls.return_value = mock_escolhas

    mock_concurso = Mock()
    mock_concurso.buscar_extracao_dados.return_value = {
        "autorizacoes-publicadas": 500
    }
    mock_concurso_cls.return_value = mock_concurso

    service = ExtracaoDadosService()
    resultado = service.extrair_total()

    assert resultado["candidatos"]["habilitados"]["total"] == 50000
    assert resultado["pendentes"] == {
        "total": 100,
        "geral": 80,
        "pcd": 10,
        "nna": 10,
    }
    mock_candidatos.buscar_extracao_dados.assert_called_once_with()
    mock_escolhas.buscar_extracao_dados.assert_called_once_with()
    mock_concurso.buscar_extracao_dados.assert_called_once_with()


@patch("relatorios.services.extracao_dados_service.ProcessoConvocacaoService")
def test_extrair_ano_sem_processos_levanta_not_found(mock_processo_cls):
    mock_processo = Mock()
    mock_processo.buscar_processos_por_concurso.return_value = (
        _processos_response(
            [
                {
                    "uuid": "proc-2025-a",
                    "data_convocacao": "2025-01-10T10:00:00Z",
                },
            ]
        )
    )
    mock_processo_cls.return_value = mock_processo

    service = ExtracaoDadosService()

    with pytest.raises(NotFound):
        service.extrair(
            concurso_uuid="a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            anos=[2026],
        )


@patch("relatorios.services.extracao_dados_service.ProcessoConvocacaoService")
def test_extrair_concurso_sem_processos_levanta_not_found(mock_processo_cls):
    mock_processo = Mock()
    mock_processo.buscar_processos_por_concurso.return_value = (
        _processos_response([])
    )
    mock_processo_cls.return_value = mock_processo

    service = ExtracaoDadosService()

    with pytest.raises(NotFound):
        service.extrair(
            concurso_uuid="a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            anos=[2026],
        )


def test_diferenca_absoluta_calcula_variacao_numerica():
    assert ExtracaoDadosService._diferenca_absoluta(80, 100) == 20.0


def test_diferenca_absoluta_arredonda_uma_casa():
    assert ExtracaoDadosService._diferenca_absoluta(3, 4.15) == 1.2


def test_calcular_pendentes_por_categoria():
    pendentes = ExtracaoDadosService._calcular_pendentes(
        {"total": 100, "geral": 70, "pcd": 20, "nna": 10},
        {"total": 40, "geral": 30, "pcd": 5, "nna": 5},
        {"total": 20, "geral": 10, "pcd": 5, "nna": 5},
        {"total": 10, "geral": 5, "pcd": 5, "nna": 0},
    )
    assert pendentes == {"total": 30, "geral": 25, "pcd": 5, "nna": 0}


def test_obter_valor_aceita_contagem_detalhada():
    assert (
        ExtracaoDadosService._obter_valor(
            {"convocados": {"total": 80, "geral": 60}}, "convocados"
        )
        == 80
    )
