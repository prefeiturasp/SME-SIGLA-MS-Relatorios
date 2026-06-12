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


@patch(
    "relatorios.services.extracao_dados_service.ConcursoService"
)
@patch(
    "relatorios.services.extracao_dados_service.EscolhasService"
)
@patch(
    "relatorios.services.extracao_dados_service.CandidatosService"
)
@patch(
    "relatorios.services.extracao_dados_service.ProcessoConvocacaoService"
)
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
        "habilitados": {"total": 10000}
    }
    mock_candidatos_cls.return_value = mock_candidatos

    mock_escolhas = Mock()
    mock_escolhas.buscar_extracao_dados.return_value = {
        "2026": {"escolha": 100}
    }
    mock_escolhas_cls.return_value = mock_escolhas

    mock_concurso = Mock()
    mock_concurso.buscar_extracao_dados.return_value = {
        "2026": {"autorizacoes-publicadas": 100}
    }
    mock_concurso_cls.return_value = mock_concurso

    service = ExtracaoDadosService(
        convocacao_base_url="http://convocacao",
        candidatos_base_url="http://candidatos",
        escolhas_base_url="http://escolhas",
        concursos_base_url="http://concursos",
    )
    resultado = service.extrair(concurso_uuid=concurso_uuid, ano=2026)

    assert resultado["candidatos"]["habilitados"]["total"] == 10000
    assert resultado["escolhas"]["2026"]["escolha"] == 100
    filtros_esperados = [
        {
            "ano": 2025,
            "processo_uuids": ["proc-2025-a"],
        },
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
        ano=2026,
    )


@patch(
    "relatorios.services.extracao_dados_service.ConcursoService"
)
@patch(
    "relatorios.services.extracao_dados_service.EscolhasService"
)
@patch(
    "relatorios.services.extracao_dados_service.CandidatosService"
)
def test_extrair_total_chama_microservicos_sem_parametros(
    mock_candidatos_cls,
    mock_escolhas_cls,
    mock_concurso_cls,
):
    mock_candidatos = Mock()
    mock_candidatos.buscar_extracao_dados.return_value = {
        "habilitados": {"total": 50000}
    }
    mock_candidatos_cls.return_value = mock_candidatos

    mock_escolhas = Mock()
    mock_escolhas.buscar_extracao_dados.return_value = {
        "2026": {"escolha": 1000}
    }
    mock_escolhas_cls.return_value = mock_escolhas

    mock_concurso = Mock()
    mock_concurso.buscar_extracao_dados.return_value = {
        "2026": {"autorizacoes-publicadas": 500}
    }
    mock_concurso_cls.return_value = mock_concurso

    service = ExtracaoDadosService(
        convocacao_base_url="http://convocacao",
        candidatos_base_url="http://candidatos",
        escolhas_base_url="http://escolhas",
        concursos_base_url="http://concursos",
    )
    resultado = service.extrair_total()

    assert resultado["candidatos"]["habilitados"]["total"] == 50000
    mock_candidatos.buscar_extracao_dados.assert_called_once_with()
    mock_escolhas.buscar_extracao_dados.assert_called_once_with()
    mock_concurso.buscar_extracao_dados.assert_called_once_with()


@patch(
    "relatorios.services.extracao_dados_service.ProcessoConvocacaoService"
)
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

    service = ExtracaoDadosService(
        convocacao_base_url="http://convocacao",
        candidatos_base_url="http://candidatos",
    )

    with pytest.raises(NotFound):
        service.extrair(
            concurso_uuid="a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            ano=2026,
        )


@patch(
    "relatorios.services.extracao_dados_service.ProcessoConvocacaoService"
)
def test_extrair_concurso_sem_processos_levanta_not_found(mock_processo_cls):
    mock_processo = Mock()
    mock_processo.buscar_processos_por_concurso.return_value = (
        _processos_response([])
    )
    mock_processo_cls.return_value = mock_processo

    service = ExtracaoDadosService(
        convocacao_base_url="http://convocacao",
        candidatos_base_url="http://candidatos",
    )

    with pytest.raises(NotFound):
        service.extrair(
            concurso_uuid="a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            ano=2026,
        )
