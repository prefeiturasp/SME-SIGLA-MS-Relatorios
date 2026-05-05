import pytest
from unittest.mock import patch
import requests

from relatorios.services.agendas_api_service import AgendasService


class _Resp:
    def __init__(self, payload=None, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code and self.status_code >= 400:
            raise requests.HTTPError(f'status={self.status_code}')


def _svc(base='http://api.local', timeout=30):
    return AgendasService(base_url=base, timeout_seconds=timeout)


@patch('relatorios.services.agendas_api_service.http_client.get')
def test_buscar_agendas_success_with_pagination_and_headers(mock_get):
    mock_resp = _Resp(payload={'results': []}, status_code=200)
    mock_get.return_value = mock_resp

    svc = _svc(timeout=5)
    resp = svc.buscar_agendas(processo_convocacao_uuid='PROC-1', page=2, page_size=50)

    assert resp is mock_resp
    mock_get.assert_called_once_with(
        'http://api.local/api/v1/agendas/',
        params={'page': 2, 'page_size': 50, 'processo_convocacao_uuid': 'PROC-1'},
        headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
        timeout=5,
    )


@patch('relatorios.services.agendas_api_service.http_client.get')
def test_buscar_agendas_respects_trailing_slash_in_base_url(mock_get):
    mock_get.return_value = _Resp(payload=[], status_code=200)

    svc = _svc(base='http://api.local/', timeout=10)
    svc.buscar_agendas(processo_convocacao_uuid='P1')

    # Verifica que a URL não fica com double slash
    called_args = mock_get.call_args.args
    assert called_args[0] == 'http://api.local/api/v1/agendas/'


@patch('relatorios.services.agendas_api_service.http_client.get')
def test_buscar_agendas_http_error_raises(mock_get):
    mock_get.return_value = _Resp(None, status_code=500)

    svc = _svc()
    with pytest.raises(requests.HTTPError):
        svc.buscar_agendas(processo_convocacao_uuid='P-ERR')


@patch('relatorios.services.agendas_api_service.http_client.get', side_effect=requests.RequestException('boom'))
def test_buscar_agendas_request_exception_is_propagated(mock_get):
    svc = _svc()
    with pytest.raises(requests.RequestException):
        svc.buscar_agendas(processo_convocacao_uuid='P-EXC')


