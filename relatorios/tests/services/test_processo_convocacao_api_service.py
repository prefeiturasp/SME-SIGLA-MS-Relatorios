import pytest
from unittest.mock import patch, Mock
import requests

from relatorios.services.processo_convocacao_api_service import ProcessoConvocacaoService


class _Resp:
    def __init__(self, payload=None, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code and self.status_code >= 400:
            raise requests.HTTPError(f'status={self.status_code}')


def _svc(base='http://api.local', timeout=12):
    return ProcessoConvocacaoService(base_url=base, timeout_seconds=timeout)


# -------- buscar_processo_convocacao ----------

@patch('relatorios.services.processo_convocacao_api_service.http_client.get')
def test_buscar_processo_convocacao_success(mock_get):
    mock_get.return_value = _Resp(payload={'uuid': 'P1'})
    svc = _svc(timeout=5)
    resp = svc.buscar_processo_convocacao('P1')
    assert resp.status_code == 200
    mock_get.assert_called_once_with(
        'http://api.local/api/v1/processos-convocacao/P1/',
        headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
        timeout=5,
    )


@patch('relatorios.services.processo_convocacao_api_service.http_client.get')
def test_buscar_processo_convocacao_http_error(mock_get):
    mock_get.return_value = _Resp(None, status_code=404)
    svc = _svc()
    with pytest.raises(requests.HTTPError):
        svc.buscar_processo_convocacao('PERR')


# -------- buscar_processos_por_concurso ----------

@patch('relatorios.services.processo_convocacao_api_service.http_client.get')
def test_buscar_processos_por_concurso_success(mock_get):
    mock_get.return_value = _Resp(payload={'results': [{'uuid': 'P1'}]})
    svc = _svc(timeout=7)
    resp = svc.buscar_processos_por_concurso('CU1')
    assert resp.status_code == 200
    mock_get.assert_called_once_with(
        'http://api.local/api/v1/processos-convocacao/',
        params={'concurso_uuid': 'CU1'},
        headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
        timeout=7,
    )


@patch('relatorios.services.processo_convocacao_api_service.http_client.get', side_effect=requests.RequestException('boom'))
def test_buscar_processos_por_concurso_request_exception(mock_get):
    svc = _svc()
    with pytest.raises(requests.RequestException):
        svc.buscar_processos_por_concurso('CUERR')


# -------- separar_processos_por_principal ----------

def test_separar_processos_por_principal_dict_results():
    svc = _svc()
    svc.buscar_processo_convocacao = Mock(return_value=_Resp({'concurso_uuid': 'CU1'}))
    svc.buscar_processos_por_concurso = Mock(return_value=_Resp({'results': [
        {'uuid': 'PMAIN'}, {'uuid': 'PX'}, {'uuid': 'PY'},
    ]}))
    processo_data = {'uuid': 'PMAIN', 'concurso_uuid': 'CU1'}
    principal, outros = svc.separar_processos_por_principal(processo_data)
    assert principal == 'PMAIN'
    assert set(outros) == {'PX', 'PY'}


def test_separar_processos_por_principal_list_shape():
    svc = _svc()
    svc.buscar_processo_convocacao = Mock(return_value=_Resp({'concurso_uuid': 'CU2'}))
    svc.buscar_processos_por_concurso = Mock(return_value=_Resp([
        {'uuid': 'PMAIN'}, {'uuid': 'PA'}, {'uuid': 'PB'},
    ]))
    processo_data = {'uuid': 'PMAIN', 'concurso_uuid': 'CU2'}
    principal, outros = svc.separar_processos_por_principal(processo_data)
    assert principal == 'PMAIN'
    assert outros == ['PA', 'PB']


def test_separar_processos_por_principal_single_object_wrapped():
    svc = _svc()
    svc.buscar_processo_convocacao = Mock(return_value=_Resp({'concurso_uuid': 'CU3'}))
    # retorna um dict simples; código deve envolver em lista
    svc.buscar_processos_por_concurso = Mock(return_value=_Resp({'uuid': 'PMAIN'}))
    processo_data = {'uuid': 'PMAIN', 'concurso_uuid': 'CU3'}
    principal, outros = svc.separar_processos_por_principal(processo_data)
    assert principal == 'PMAIN'
    assert outros == []


def test_separar_processos_por_principal_missing_concurso_raises_value_error():
    svc = _svc()
    svc.buscar_processo_convocacao = Mock(return_value=_Resp({}))  # sem concurso_uuid
    processo_data = {'uuid': 'PMAIN'}  # sem concurso_uuid
    with pytest.raises(ValueError):
        svc.separar_processos_por_principal(processo_data)


