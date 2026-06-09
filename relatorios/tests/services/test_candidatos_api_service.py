"""Módulo tests/services/test_candidatos_api_service."""
from __future__ import annotations
from typing import Any
from unittest.mock import patch
import pytest
import requests
from relatorios.services.candidatos_api_service import CandidatosService

class _Resp:
    """Define _Resp."""

    def __init__(self, payload: Any, status_code: Any=200) -> None:
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

def _svc() -> Any:
    """Executa  svc.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return CandidatosService(base_url='http://api.local', timeout_seconds=5)

@patch('relatorios.services.candidatos_api_service.http_client.get')
def test_buscar_habilitados_single_codigo(mock_get: Any) -> None:
    """Verifica buscar habilitados single codigo.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_resp = _Resp([{'uuid': 'a'}])
    mock_get.return_value = mock_resp
    svc = _svc()
    resp = svc.buscar_habilitados(processo_uuid='proc1', codigo_cargo='123', ordering='ranking_escolha')
    assert resp is mock_resp
    mock_get.assert_called_once_with('http://api.local/api/v1/habilitados/', params={'processo_uuid': 'proc1', 'ordering': 'ranking_escolha', 'codigo_cargo': '123'}, headers={'Accept': 'application/json', 'Content-Type': 'application/json'}, timeout=5)

@patch('relatorios.services.candidatos_api_service.http_client.get')
def test_buscar_habilitados_multi_codigos_usa_in(mock_get: Any) -> None:
    """Verifica buscar habilitados multi codigos usa in.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_resp = _Resp([])
    mock_get.return_value = mock_resp
    svc = _svc()
    svc.buscar_habilitados(processo_uuid='proc2', codigo_cargo=['111', '222'])
    called_kwargs = mock_get.call_args.kwargs
    assert called_kwargs['params']['codigo_cargo__in'] == '111,222'
    assert 'codigo_cargo' not in called_kwargs['params']

@patch('relatorios.services.candidatos_api_service.http_client.get')
def test_buscar_habilitados_http_error(mock_get: Any) -> None:
    """Verifica buscar habilitados http error.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_resp = _Resp(None, status_code=500)
    mock_get.return_value = mock_resp
    svc = _svc()
    with pytest.raises(requests.HTTPError):
        svc.buscar_habilitados(processo_uuid='proc1')

@patch('relatorios.services.candidatos_api_service.http_client.get')
def test_buscar_habilitados_por_processos_e_classificacoes_success(mock_get: Any) -> None:
    """Verifica buscar habilitados por processos e classificacoes success.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_resp = _Resp([{'uuid': 'x'}])
    mock_get.return_value = mock_resp
    svc = _svc()
    resp = svc.buscar_habilitados_por_processos_e_classificacoes(processo_uuids=['p1', 'p2'], classificacao=[1, 2], classificacao_nna='3', codigo_cargo=['10', '20'], ordering='ranking_escolha')
    assert resp is mock_resp
    called = mock_get.call_args.kwargs['params']
    assert called['processo_uuid__in'] == 'p1,p2'
    assert called['classificacao__in'] == '1,2'
    assert called['classificacao_nna'] == '3'
    assert called['codigo_cargo__in'] == '10,20'
    assert called['ordering'] == 'ranking_escolha'

@patch('relatorios.services.candidatos_api_service.http_client.get')
def test_buscar_habilitados_por_processos_e_classificacoes_http_error(mock_get: Any) -> None:
    """Verifica buscar habilitados por processos e classificacoes http error.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_resp = _Resp(None, status_code=404)
    mock_get.return_value = mock_resp
    svc = _svc()
    with pytest.raises(requests.HTTPError):
        svc.buscar_habilitados_por_processos_e_classificacoes(processo_uuids='p1')

@patch('relatorios.services.candidatos_api_service.http_client.get')
def test_bhpec_processo_uuid_single_list_uses_param(mock_get: Any) -> None:
    """Verifica bhpec processo uuid single list uses param.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_get.return_value = _Resp([])
    svc = _svc()
    svc.buscar_habilitados_por_processos_e_classificacoes(processo_uuids=['only-one'])
    called = mock_get.call_args.kwargs['params']
    assert called['processo_uuid'] == 'only-one'
    assert 'processo_uuid__in' not in called

@patch('relatorios.services.candidatos_api_service.http_client.get')
def test_bhpec_processo_uuid_csv_string_uses_in(mock_get: Any) -> None:
    """Verifica bhpec processo uuid csv string uses in.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_get.return_value = _Resp([])
    svc = _svc()
    svc.buscar_habilitados_por_processos_e_classificacoes(processo_uuids='p1,p2')
    called = mock_get.call_args.kwargs['params']
    assert called['processo_uuid__in'] == 'p1,p2'
    assert 'processo_uuid' not in called

@patch('relatorios.services.candidatos_api_service.http_client.get')
def test_bhpec_classificacao_single_list_sets_plain(mock_get: Any) -> None:
    """Verifica bhpec classificacao single list sets plain.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_get.return_value = _Resp([])
    svc = _svc()
    svc.buscar_habilitados_por_processos_e_classificacoes(processo_uuids=['p1', 'p2'], classificacao=[7])
    called = mock_get.call_args.kwargs['params']
    assert called['classificacao'] == '7'
    assert 'classificacao__in' not in called

@patch('relatorios.services.candidatos_api_service.http_client.get')
def test_bhpec_classificacao_csv_string_sets_in(mock_get: Any) -> None:
    """Verifica bhpec classificacao csv string sets in.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_get.return_value = _Resp([])
    svc = _svc()
    svc.buscar_habilitados_por_processos_e_classificacoes(processo_uuids='p1', classificacao='1,2')
    called = mock_get.call_args.kwargs['params']
    assert called['classificacao__in'] == '1,2'
    assert 'classificacao' not in called

@patch('relatorios.services.candidatos_api_service.http_client.get')
def test_bhpec_classificacao_nna_single_list_sets_plain(mock_get: Any) -> None:
    """Verifica bhpec classificacao nna single list sets plain.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_get.return_value = _Resp([])
    svc = _svc()
    svc.buscar_habilitados_por_processos_e_classificacoes(processo_uuids='p1', classificacao_nna=[3])
    called = mock_get.call_args.kwargs['params']
    assert called['classificacao_nna'] == '3'
    assert 'classificacao_nna__in' not in called

@patch('relatorios.services.candidatos_api_service.http_client.get')
def test_bhpec_classificacao_nna_csv_string_sets_in(mock_get: Any) -> None:
    """Verifica bhpec classificacao nna csv string sets in.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_get.return_value = _Resp([])
    svc = _svc()
    svc.buscar_habilitados_por_processos_e_classificacoes(processo_uuids='p1', classificacao_nna='3,4')
    called = mock_get.call_args.kwargs['params']
    assert called['classificacao_nna__in'] == '3,4'
    assert 'classificacao_nna' not in called

@patch('relatorios.services.candidatos_api_service.http_client.get')
def test_bhpec_codigo_cargo_string_paths(mock_get: Any) -> None:
    """Verifica bhpec codigo cargo string paths.
    
    Args:
        mock_get: Parâmetro mock get da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_get.return_value = _Resp([])
    svc = _svc()
    svc.buscar_habilitados_por_processos_e_classificacoes(processo_uuids='p1', codigo_cargo='10,20')
    called = mock_get.call_args.kwargs['params']
    assert called['codigo_cargo__in'] == '10,20'
    assert 'codigo_cargo' not in called
    svc.buscar_habilitados_por_processos_e_classificacoes(processo_uuids='p1', codigo_cargo='10')
    called2 = mock_get.call_args.kwargs['params']
    assert called2['codigo_cargo'] == '10'
    assert 'codigo_cargo__in' not in called2

@patch('relatorios.services.candidatos_api_service.http_client.post')
def test_buscar_por_uuids_success(mock_post: Any) -> None:
    """Verifica buscar por uuids success.
    
    Args:
        mock_post: Parâmetro mock post da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_resp = _Resp({'results': [{'uuid': 'a'}]})
    mock_post.return_value = mock_resp
    svc = _svc()
    resp = svc.buscar_por_uuids(uuids=['u1', 'u2'], order_by='ranking')
    assert resp is mock_resp
    mock_post.assert_called_once_with('http://api.local/api/v1/habilitados/buscar-por-uuids/', params={'order_by': 'ranking'}, json={'uuids': ['u1', 'u2']}, headers={'Accept': 'application/json', 'Content-Type': 'application/json'}, timeout=5)

@patch('relatorios.services.candidatos_api_service.http_client.post')
def test_buscar_por_uuids_http_error(mock_post: Any) -> None:
    """Verifica buscar por uuids http error.
    
    Args:
        mock_post: Parâmetro mock post da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    mock_resp = _Resp(None, status_code=400)
    mock_post.return_value = mock_resp
    svc = _svc()
    with pytest.raises(requests.HTTPError):
        svc.buscar_por_uuids(uuids=['u1'])

def test_buscar_candidatos_por_agendas_success_extracts_both_formats(monkeypatch: Any) -> Any:
    """Verifica buscar candidatos por agendas success extracts both formats.
    
    Args:
        monkeypatch: Fixture do pytest para substituir objetos.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    svc = _svc()
    agendas_response = _Resp({'results': [{'uuid': 'a1', 'candidatos_uuids': []}, {'uuid': 'a2', 'candidatos_uuids': ['x', 'y']}]})
    calls = []

    def _mock_buscar_por_uuids(uuids: Any, order_by: Any='ranking_escolha') -> Any:
        """Executa  mock buscar por uuids.
        
        Args:
            uuids: Parâmetro uuids da operação.
            order_by: Parâmetro order by da operação.
        
        Returns:
            Resultado da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        calls.append(list(uuids))
        if uuids == ['x', 'y']:
            return _Resp({'results': [{'uuid': 'x'}, {'uuid': 'y'}]})
        return _Resp([])
    monkeypatch.setattr(CandidatosService, 'buscar_por_uuids', staticmethod(_mock_buscar_por_uuids))
    resultado = svc.buscar_candidatos_por_agendas(agendas_response, order_by='ranking')
    assert 'agendas' in resultado and len(resultado['agendas']) == 2
    assert resultado['agendas'][0]['candidatos'] == []
    assert [c['uuid'] for c in resultado['agendas'][1]['candidatos']] == ['x', 'y']
    assert calls == [['x', 'y']]

def test_buscar_candidatos_por_agendas_handles_request_exception(monkeypatch: Any) -> None:
    """Verifica buscar candidatos por agendas handles request exception.
    
    Args:
        monkeypatch: Fixture do pytest para substituir objetos.
    
    Returns:
        Não retorna valor.
    
    Raises:
        RequestException: Se ocorrer erro nesta operação.
    """
    svc = _svc()
    agendas_response = _Resp([{'uuid': 'a1', 'candidatos_uuids': ['z']}])

    def _raise(*args: Any, **kwargs: Any) -> None:
        """Executa  raise.
        
        Args:
            *args: Argumentos posicionais variáveis.
            **kwargs: Argumentos nomeados variáveis.
        
        Returns:
            Não retorna valor.
        
        Raises:
            RequestException: Se ocorrer erro nesta operação.
        """
        raise requests.RequestException('boom')
    monkeypatch.setattr(CandidatosService, 'buscar_por_uuids', staticmethod(_raise))
    resultado = svc.buscar_candidatos_por_agendas(agendas_response)
    assert len(resultado['agendas']) == 1
    assert resultado['agendas'][0]['candidatos'] == []
    assert 'erro' in resultado['agendas'][0]
