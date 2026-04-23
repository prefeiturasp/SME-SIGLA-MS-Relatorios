import pytest
from unittest.mock import patch
import requests

from relatorios.services.processos_api_service import ProcessosService


class _Resp:
    def __init__(self, payload=None, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code and self.status_code >= 400:
            raise requests.HTTPError(f'status={self.status_code}')


def _svc(base='http://api.local', timeout=9):
    return ProcessosService(base_url=base, timeout_seconds=timeout)


@patch('relatorios.services.processos_api_service.http_client.get')
def test_buscar_cargos_por_processo_success(mock_get):
    mock_get.return_value = _Resp(payload={'cargos': []})
    svc = _svc(timeout=4)
    resp = svc.buscar_cargos_por_processo('P123')
    assert resp.status_code == 200
    mock_get.assert_called_once_with(
        'http://api.local/api/v1/processos-convocacao/P123/cargos/',
        headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
        timeout=4,
    )


@patch('relatorios.services.processos_api_service.http_client.get')
def test_buscar_cargos_por_processo_http_error(mock_get):
    mock_get.return_value = _Resp(None, status_code=502)
    svc = _svc()
    with pytest.raises(requests.HTTPError):
        svc.buscar_cargos_por_processo('PERR')


