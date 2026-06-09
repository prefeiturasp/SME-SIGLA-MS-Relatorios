"""Módulo tests/services/test_processo_convocacao_api_service."""
from __future__ import annotations
from typing import Any
from unittest.mock import Mock, patch
import pytest
import requests
from relatorios.services.processo_convocacao_api_service import ProcessoConvocacaoService

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

def _svc(base: Any='http://api.local', timeout: Any=12) -> Any:
    """Executa  svc.
    
    Args:
        base: Parâmetro base da operação.
        timeout: Parâmetro timeout da operação.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return ProcessoConvocacaoService(base_url=base, timeout_seconds=timeout)

@patch('relatorios.services.processo_convocacao_api_service.http_client.get')
def test_buscar_processo_convocacao_success(mock_get: Any) -> None:
    """Verifica buscar processo convocacao success.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_get.return_value = _Resp(payload={'uuid': 'P1'})
    svc = _svc(timeout=5)
    resp = svc.buscar_processo_convocacao('P1')
    assert resp.status_code == 200
    mock_get.assert_called_once_with('http://api.local/api/v1/processos-convocacao/P1/', headers={'Accept': 'application/json', 'Content-Type': 'application/json'}, timeout=5)

@patch('relatorios.services.processo_convocacao_api_service.http_client.get')
def test_buscar_processo_convocacao_http_error(mock_get: Any) -> None:
    """Verifica buscar processo convocacao http error.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_get.return_value = _Resp(None, status_code=404)
    svc = _svc()
    with pytest.raises(requests.HTTPError):
        svc.buscar_processo_convocacao('PERR')

@patch('relatorios.services.processo_convocacao_api_service.http_client.get')
def test_buscar_processos_por_concurso_success(mock_get: Any) -> None:
    """Verifica buscar processos por concurso success.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_get.return_value = _Resp(payload={'results': [{'uuid': 'P1'}]})
    svc = _svc(timeout=7)
    resp = svc.buscar_processos_por_concurso('CU1')
    assert resp.status_code == 200
    mock_get.assert_called_once_with('http://api.local/api/v1/processos-convocacao/', params={'concurso_uuid': 'CU1'}, headers={'Accept': 'application/json', 'Content-Type': 'application/json'}, timeout=7)

@patch('relatorios.services.processo_convocacao_api_service.http_client.get', side_effect=requests.RequestException('boom'))
def test_buscar_processos_por_concurso_request_exception(mock_get: Any) -> None:
    """Verifica buscar processos por concurso request exception.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    svc = _svc()
    with pytest.raises(requests.RequestException):
        svc.buscar_processos_por_concurso('CUERR')

def test_separar_processos_por_principal_dict_results() -> None:
    """Verifica separar processos por principal dict results.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    svc = _svc()
    svc.buscar_processo_convocacao = Mock(return_value=_Resp({'concurso_uuid': 'CU1'}))
    svc.buscar_processos_por_concurso = Mock(return_value=_Resp({'results': [{'uuid': 'PMAIN'}, {'uuid': 'PX'}, {'uuid': 'PY'}]}))
    processo_data = {'uuid': 'PMAIN', 'concurso_uuid': 'CU1'}
    principal, outros = svc.separar_processos_por_principal(processo_data)
    assert principal == 'PMAIN'
    assert set(outros) == {'PX', 'PY'}

def test_separar_processos_por_principal_list_shape() -> None:
    """Verifica separar processos por principal list shape.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    svc = _svc()
    svc.buscar_processo_convocacao = Mock(return_value=_Resp({'concurso_uuid': 'CU2'}))
    svc.buscar_processos_por_concurso = Mock(return_value=_Resp([{'uuid': 'PMAIN'}, {'uuid': 'PA'}, {'uuid': 'PB'}]))
    processo_data = {'uuid': 'PMAIN', 'concurso_uuid': 'CU2'}
    principal, outros = svc.separar_processos_por_principal(processo_data)
    assert principal == 'PMAIN'
    assert outros == ['PA', 'PB']

def test_separar_processos_por_principal_single_object_wrapped() -> None:
    """Verifica separar processos por principal single object wrapped.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    svc = _svc()
    svc.buscar_processo_convocacao = Mock(return_value=_Resp({'concurso_uuid': 'CU3'}))
    svc.buscar_processos_por_concurso = Mock(return_value=_Resp({'uuid': 'PMAIN'}))
    processo_data = {'uuid': 'PMAIN', 'concurso_uuid': 'CU3'}
    principal, outros = svc.separar_processos_por_principal(processo_data)
    assert principal == 'PMAIN'
    assert outros == []

def test_separar_processos_por_principal_missing_concurso_raises_value_error() -> None:
    """Verifica separar processos por principal missing concurso raises value error.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    svc = _svc()
    svc.buscar_processo_convocacao = Mock(return_value=_Resp({}))
    processo_data = {'uuid': 'PMAIN'}
    with pytest.raises(ValueError):
        svc.separar_processos_por_principal(processo_data)
