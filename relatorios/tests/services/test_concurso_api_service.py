from unittest.mock import patch

import pytest
import requests

from relatorios.services.concurso_api_service import ConcursoService


class _Resp:
    def __init__(self, payload=None, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code and self.status_code >= 400:
            raise requests.HTTPError(f"status={self.status_code}")


def _svc(base="http://api.local", timeout=15):
    return ConcursoService(base_url=base, timeout_seconds=timeout)


@patch("relatorios.services.concurso_api_service.http_client.post")
def test_buscar_extracao_dados_success(mock_post):
    mock_post.return_value = _Resp(
        payload={"concurso": {"nome": "Concurso X", "codigo": 1001}}
    )
    svc = _svc(timeout=5)
    resp = svc.buscar_extracao_dados(
        concurso_uuid="a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
        ano=2026,
    )
    assert resp == {"concurso": {"nome": "Concurso X", "codigo": 1001}}
    mock_post.assert_called_once_with(
        "http://api.local/api/v1/extracao-dados/",
        json={
            "concurso_uuid": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            "ano": 2026,
        },
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=5,
    )


@patch("relatorios.services.concurso_api_service.http_client.post")
def test_buscar_extracao_dados_sem_parametros(mock_post):
    mock_post.return_value = _Resp(
        payload={"2026": {"autorizacoes-publicadas": 500}}
    )
    svc = _svc(timeout=5)
    resp = svc.buscar_extracao_dados()
    assert resp == {"2026": {"autorizacoes-publicadas": 500}}
    mock_post.assert_called_once_with(
        "http://api.local/api/v1/extracao-dados/",
        json={},
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        timeout=5,
    )


@patch("relatorios.services.concurso_api_service.http_client.post")
def test_buscar_extracao_dados_http_error(mock_post):
    mock_post.return_value = _Resp(None, status_code=500)
    svc = _svc()
    with pytest.raises(requests.HTTPError):
        svc.buscar_extracao_dados(
            concurso_uuid="a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
            ano=2026,
        )
