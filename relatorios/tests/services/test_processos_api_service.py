"""Módulo tests/services/test_processos_api_service."""
from __future__ import annotations
from typing import Any
from unittest.mock import patch
import pytest
import requests
from relatorios.services.processos_api_service import ProcessosService

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

def _svc(base: Any='http://api.local', timeout: Any=9) -> Any:
    """Executa  svc.
    
    Args:
        base: Parâmetro base da operação.
        timeout: Parâmetro timeout da operação.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return ProcessosService(base_url=base, timeout_seconds=timeout)

@patch('relatorios.services.processos_api_service.http_client.get')
def test_buscar_cargos_por_processo_success(mock_get: Any) -> None:
    """Verifica buscar cargos por processo success.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_get.return_value = _Resp(payload={'cargos': []})
    svc = _svc(timeout=4)
    resp = svc.buscar_cargos_por_processo('P123')
    assert resp.status_code == 200
    mock_get.assert_called_once_with('http://api.local/api/v1/processos-convocacao/P123/cargos/', headers={'Accept': 'application/json', 'Content-Type': 'application/json'}, timeout=4)

@patch('relatorios.services.processos_api_service.http_client.get')
def test_buscar_cargos_por_processo_http_error(mock_get: Any) -> None:
    """Verifica buscar cargos por processo http error.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_get.return_value = _Resp(None, status_code=502)
    svc = _svc()
    with pytest.raises(requests.HTTPError):
        svc.buscar_cargos_por_processo('PERR')
