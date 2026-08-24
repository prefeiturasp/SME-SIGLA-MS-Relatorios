"""Módulo tests/services/test_processos_api_service."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
import requests

from relatorios.services.processos_api_service import ProcessosService


class _Resp:
    """Representa Resp."""

    def __init__(self, payload: Any = None, status_code: Any = 200) -> None:
        """Inicializa a instância com os parâmetros informados."""
        self._payload = payload
        self.status_code = status_code

    def json(self) -> Any:
        """Json."""
        return self._payload

    def raise_for_status(self) -> None:
        """Raise for status."""
        if self.status_code and self.status_code >= 400:
            raise requests.HTTPError(f"status={self.status_code}")


def _svc(
    monkeypatch: Any,
    base: Any = "http://api.local",
    timeout: Any = 9,
) -> Any:
    """Svc."""
    monkeypatch.setattr(ProcessosService, "base_url", base.rstrip("/"))
    monkeypatch.setattr(ProcessosService, "timeout_seconds", timeout)
    monkeypatch.setattr(
        ProcessosService,
        "_headers",
        {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-Key": "test-key",
        },
    )
    return ProcessosService()


@patch("relatorios.services.processos_api_service.http_client.get")
def test_buscar_cargos_por_processo_success(
    mock_get: Any,
    monkeypatch: Any,
) -> None:
    """Verifica buscar cargos por processo success."""
    mock_get.return_value = _Resp(payload={"cargos": []})
    svc = _svc(monkeypatch, timeout=4)
    resp = svc.buscar_cargos_por_processo("P123")
    assert resp.status_code == 200
    mock_get.assert_called_once_with(
        "http://api.local/api/v1/processos-convocacao/P123/cargos/",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-Key": "test-key",
        },
        timeout=4,
    )


@patch("relatorios.services.processos_api_service.http_client.get")
def test_buscar_cargos_por_processo_http_error(
    mock_get: Any,
    monkeypatch: Any,
) -> None:
    """Verifica buscar cargos por processo http error."""
    mock_get.return_value = _Resp(None, status_code=502)
    svc = _svc(monkeypatch)
    with pytest.raises(requests.HTTPError):
        svc.buscar_cargos_por_processo("PERR")
