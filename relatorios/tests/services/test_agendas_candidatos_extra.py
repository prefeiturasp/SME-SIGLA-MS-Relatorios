"""Módulo tests/services/test_agendas_candidatos_extra."""
from __future__ import annotations
from typing import Any
from unittest.mock import patch
import pytest
import requests
from relatorios.services.agendas_api_service import AgendasService
from relatorios.services.candidatos_api_service import CandidatosService

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
        if self.status_code >= 400:
            raise requests.HTTPError(f'status={self.status_code}')

@patch('relatorios.services.agendas_api_service.http_client.get')
def test_buscar_agenda_por_uuid_success_and_error(mock_get: Any) -> None:
    """Verifica buscar agenda por uuid success and error.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    svc = AgendasService(base_url='http://api.local', timeout_seconds=9)
    ok = _Resp({'uuid': 'ag1'})
    mock_get.return_value = ok
    assert svc.buscar_agenda_por_uuid('ag1') is ok
    mock_get.return_value = _Resp(status_code=404)
    with pytest.raises(requests.HTTPError):
        svc.buscar_agenda_por_uuid('ag2')

@patch('relatorios.services.candidatos_api_service.http_client.get')
def test_candidatos_extra_endpoints_success(mock_get: Any) -> None:
    """Verifica candidatos extra endpoints success.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    svc = CandidatosService(base_url='http://api.local', timeout_seconds=7)
    mock_get.return_value = _Resp({'results': []})
    assert svc.buscar_concurso_candidatos_por_processo('proc-1').status_code == 200
    assert svc.buscar_reclassificados_por_concurso('conc-1', 'proc-1').status_code == 200
    assert svc.buscar_eliminados_por_concurso('conc-1', 'proc-1', 100, 1).status_code == 200

@patch('relatorios.services.candidatos_api_service.http_client.get')
def test_candidatos_extra_endpoints_http_error(mock_get: Any) -> None:
    """Verifica candidatos extra endpoints http error.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    svc = CandidatosService(base_url='http://api.local')
    mock_get.return_value = _Resp(status_code=500)
    with pytest.raises(requests.HTTPError):
        svc.buscar_concurso_candidatos_por_processo('proc-err')
    with pytest.raises(requests.HTTPError):
        svc.buscar_reclassificados_por_concurso('conc-err', 'proc-err')
    with pytest.raises(requests.HTTPError):
        svc.buscar_eliminados_por_concurso('conc-err', 'proc-err', 10, 1)

def test_buscar_candidatos_por_agendas_invalid_payload_raises() -> None:
    """Verifica buscar candidatos por agendas invalid payload raises.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    svc = CandidatosService(base_url='http://api.local')
    broken = _Resp()
    broken.json = lambda: (_ for _ in ()).throw(ValueError('json quebrado'))  # type: ignore[method-assign]
    with pytest.raises(ValueError):
        svc.buscar_candidatos_por_agendas(broken)  # type: ignore[arg-type]
