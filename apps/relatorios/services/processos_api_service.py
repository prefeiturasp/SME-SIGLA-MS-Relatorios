"""Serviços para integração com API de processos de convocação."""

from __future__ import annotations

import logging

import requests
from django.conf import settings
from requests import RequestException
from sigla_sdk.context import get_correlation_id
from sigla_sdk.http.api_client import http_client

logger = logging.getLogger(__name__)


class ProcessosService:
    """Serviço para operações de processos."""

    base_url = settings.PROCESSOS_API_URL.rstrip("/")
    timeout_seconds = 30
    _headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        settings.API_KEY_HEADER: settings.PROCESSOS_API_KEY,
    }

    def buscar_cargos_por_processo(
        self, processo_uuid: str
    ) -> requests.Response:
        """Busca cargos por processo.

        Args:
            processo_uuid: UUID do processo de convocação.

        Returns:
            Resposta HTTP com o arquivo para download.
        """
        url = f"{self.base_url}/api/v1/processos-convocacao/{processo_uuid}/cargos/"  # noqa: E501
        logger.info(
            "Buscando cargos do processo",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
                "url": url,
                "headers": self._headers,
                "processo_uuid": processo_uuid,
            },
        )
        try:
            response = http_client.get(
                url,
                headers=self._headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except RequestException as exc:
            logger.error("Erro ao buscar cargos do processo: %s", exc)
            raise
        logger.info(
            "Cargos do processo encontrados",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
                "url": url,
                "headers": self._headers,
                "processo_uuid": processo_uuid,
                "status_code": response.status_code,
                "response": str(response.json())[:100],
            },
        )
        return response  # type: ignore[no-any-return]
