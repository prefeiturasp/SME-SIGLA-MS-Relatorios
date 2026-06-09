"""Módulo tests/services/test_agendas_api_service."""
from __future__ import annotations
from typing import Any
from unittest.mock import patch
import pytest
import requests
from relatorios.services.agendas_api_service import AgendasService

class _Resp:
    """Define _Resp."""

    def __init__(self, payload: Any=None, status_code: Any=200) -> None:
        """Executa   init  .
        
        Args:
            self: Instância do objeto.
            payload: Parâmetro payload da operação.
            status_code: Parâmetro status code da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        self._payload = payload
        self.status_code = status_code

    def json(self) -> Any:
        """Executa json.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Resultado da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        return self._payload

    def raise_for_status(self) -> None:
        """Executa raise for status.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Não retorna valor.
        
        Raises:
            HTTPError: Se ocorrer erro nesta operação.
        """
        if self.status_code and self.status_code >= 400:
            raise requests.HTTPError(f'status={self.status_code}')

def _svc(base: Any='http://api.local', timeout: Any=30) -> Any:
    """Executa  svc.
    
    Args:
        base: Parâmetro base da operação.
        timeout: Parâmetro timeout da operação.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return AgendasService(base_url=base, timeout_seconds=timeout)

@patch('relatorios.services.agendas_api_service.http_client.get')
def test_buscar_agendas_success_with_pagination_and_headers(mock_get: Any) -> None:
    """Verifica buscar agendas success with pagination and headers.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_resp = _Resp(payload={'results': []}, status_code=200)
    mock_get.return_value = mock_resp
    svc = _svc(timeout=5)
    resp = svc.buscar_agendas(processo_convocacao_uuid='PROC-1', page=2, page_size=50)
    assert resp is mock_resp
    mock_get.assert_called_once_with('http://api.local/api/v1/agendas/', params={'page': 2, 'page_size': 50, 'processo_convocacao_uuid': 'PROC-1'}, headers={'Accept': 'application/json', 'Content-Type': 'application/json'}, timeout=5)

@patch('relatorios.services.agendas_api_service.http_client.get')
def test_buscar_agendas_respects_trailing_slash_in_base_url(mock_get: Any) -> None:
    """Verifica buscar agendas respects trailing slash in base url.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_get.return_value = _Resp(payload=[], status_code=200)
    svc = _svc(base='http://api.local/', timeout=10)
    svc.buscar_agendas(processo_convocacao_uuid='P1')
    called_args = mock_get.call_args.args
    assert called_args[0] == 'http://api.local/api/v1/agendas/'

@patch('relatorios.services.agendas_api_service.http_client.get')
def test_buscar_agendas_http_error_raises(mock_get: Any) -> None:
    """Verifica buscar agendas http error raises.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_get.return_value = _Resp(None, status_code=500)
    svc = _svc()
    with pytest.raises(requests.HTTPError):
        svc.buscar_agendas(processo_convocacao_uuid='P-ERR')

@patch('relatorios.services.agendas_api_service.http_client.get', side_effect=requests.RequestException('boom'))
def test_buscar_agendas_request_exception_is_propagated(mock_get: Any) -> None:
    """Verifica buscar agendas request exception is propagated.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    svc = _svc()
    with pytest.raises(requests.RequestException):
        svc.buscar_agendas(processo_convocacao_uuid='P-EXC')
