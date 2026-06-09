"""Módulo tests/services/test_escolhas_api_service."""
from __future__ import annotations
from typing import Any
from unittest.mock import patch
import pytest
import requests
from relatorios.services.escolhas_api_service import EscolhasService

class _Resp:
    """Define _Resp."""

    def __init__(self, payload: Any=None, status_code: Any=200) -> None:
        """Executa   init  ."""
        self._payload = payload
        self.status_code = status_code

    def json(self) -> Any:
        """Executa json."""
        return self._payload

    def raise_for_status(self) -> None:
        """Executa raise for status."""
        if self.status_code and self.status_code >= 400:
            raise requests.HTTPError(f'status={self.status_code}')

def _svc(base: Any='http://api.local', timeout: Any=15) -> Any:
    """Executa  svc."""
    return EscolhasService(base_url=base, timeout_seconds=timeout)

@patch('relatorios.services.escolhas_api_service.http_client.get')
def test_buscar_vagas_escolas_success(mock_get: Any) -> None:
    """Verifica buscar vagas escolas success."""
    mock_get.return_value = _Resp(payload={'results': []})
    svc = _svc(timeout=5)
    resp = svc.buscar_vagas_escolas(processo_uuid='PROC-123')
    assert resp.status_code == 200
    mock_get.assert_called_once_with('http://api.local/api/v1/vagas-escolas/', params={'processo_uuid': 'PROC-123'}, headers={'Accept': 'application/json', 'Content-Type': 'application/json'}, timeout=5)

@patch('relatorios.services.escolhas_api_service.http_client.get')
def test_buscar_vagas_escolas_trailing_slash_base_url(mock_get: Any) -> None:
    """Verifica buscar vagas escolas trailing slash base url."""
    mock_get.return_value = _Resp(payload=[])
    svc = _svc(base='http://api.local/')
    svc.buscar_vagas_escolas(processo_uuid='P1')
    assert mock_get.call_args.args[0] == 'http://api.local/api/v1/vagas-escolas/'

@patch('relatorios.services.escolhas_api_service.http_client.get')
def test_buscar_vagas_escolas_http_error(mock_get: Any) -> None:
    """Verifica buscar vagas escolas http error."""
    mock_get.return_value = _Resp(None, status_code=500)
    svc = _svc()
    with pytest.raises(requests.HTTPError):
        svc.buscar_vagas_escolas(processo_uuid='PERR')

@patch('relatorios.services.escolhas_api_service.http_client.get', side_effect=requests.RequestException('boom'))
def test_buscar_vagas_escolas_request_exception(mock_get: Any) -> None:
    """Verifica buscar vagas escolas request exception."""
    svc = _svc()
    with pytest.raises(requests.RequestException):
        svc.buscar_vagas_escolas(processo_uuid='PERR')

@patch('relatorios.services.escolhas_api_service.http_client.post')
def test_buscar_escolhas_por_candidatos_success_list_default_filter(mock_post: Any) -> None:
    """Verifica buscar escolhas por candidatos success list default filter."""
    payload = [{'uuid': 'u1', 'situacao': 'nao-escolha'}, {'uuid': 'u2', 'situacao': 'reconvocacao'}]
    mock_post.return_value = _Resp(payload=payload)
    svc = _svc(timeout=3)
    out = svc.buscar_escolhas_por_candidatos(candidato_uuids=['c1', 'c2'])
    assert out == [{'uuid': 'u1', 'situacao': 'nao-escolha'}]
    mock_post.assert_called_once_with('http://api.local/api/v1/escolhas/busca/', json={'candidato_uuid': ['c1', 'c2']}, headers={'Accept': 'application/json', 'Content-Type': 'application/json'}, timeout=3)

@patch('relatorios.services.escolhas_api_service.http_client.post')
def test_buscar_escolhas_por_candidatos_success_dict_results_custom_situacao(mock_post: Any) -> None:
    """Verifica buscar escolhas por candidatos success dict results custom situacao."""
    payload = {'results': [{'uuid': 'u1', 'situacao': 'reconvocacao'}, {'uuid': 'u2', 'situacao': 'nao-escolha'}]}
    mock_post.return_value = _Resp(payload=payload)
    svc = _svc()
    out = svc.buscar_escolhas_por_candidatos(candidato_uuids=['x', 'y'], situacao='reconvocacao')
    assert out == [{'uuid': 'u1', 'situacao': 'reconvocacao'}]

@patch('relatorios.services.escolhas_api_service.http_client.post')
def test_buscar_escolhas_por_candidatos_unexpected_payload_returns_empty(mock_post: Any) -> None:
    """Verifica buscar escolhas por candidatos unexpected payload returns empty."""
    mock_post.return_value = _Resp(payload={'unexpected': True})
    svc = _svc()
    out = svc.buscar_escolhas_por_candidatos(candidato_uuids=['a'])
    assert out == []

@patch('relatorios.services.escolhas_api_service.http_client.post')
def test_buscar_escolhas_por_candidatos_http_error(mock_post: Any) -> None:
    """Verifica buscar escolhas por candidatos http error."""
    mock_post.return_value = _Resp(None, status_code=400)
    svc = _svc()
    with pytest.raises(requests.HTTPError):
        svc.buscar_escolhas_por_candidatos(candidato_uuids=['a'])

@patch('relatorios.services.escolhas_api_service.http_client.post', side_effect=requests.RequestException('boom'))
def test_buscar_escolhas_por_candidatos_request_exception(mock_post: Any) -> None:
    """Verifica buscar escolhas por candidatos request exception."""
    svc = _svc()
    with pytest.raises(requests.RequestException):
        svc.buscar_escolhas_por_candidatos(candidato_uuids=['a'])
