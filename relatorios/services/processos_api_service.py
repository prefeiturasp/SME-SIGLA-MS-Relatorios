"""Serviços para integração com API de processos de convocação."""
from __future__ import annotations
from typing import Any
import logging
import requests
from requests import RequestException
from sigla_sdk.context import get_correlation_id
from sigla_sdk.http.api_client import http_client
logger = logging.getLogger(__name__)

class ProcessosService:
    """Define ProcessosService."""

    def __init__(self, base_url: str='https://example.com', timeout_seconds: int=30) -> None:
        """Executa   init  ."""
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self._default_headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def buscar_cargos_por_processo(self, processo_uuid: str) -> requests.Response:
        """Busca cargos do processo de convocação por processo_uuid.

        Args:
            processo_uuid: UUID do processo de convocação
        Returns:
            Response da API com os cargos do processo
        Raises:
            RequestException: Em caso de erro na requisição.
        """
        url = f'{self.base_url}/api/v1/processos-convocacao/{processo_uuid}/cargos/'
        logger.info('Buscando cargos do processo', extra={'correlation_id': get_correlation_id(), 'method': 'GET', 'url': url, 'headers': self._default_headers, 'processo_uuid': processo_uuid})
        try:
            response = http_client.get(url, headers=self._default_headers, timeout=self.timeout_seconds)
            response.raise_for_status()
        except RequestException as exc:
            logger.error('Erro ao buscar cargos do processo: %s', exc)
            raise
        logger.info('Cargos do processo encontrados', extra={'correlation_id': get_correlation_id(), 'method': 'GET', 'url': url, 'headers': self._default_headers, 'processo_uuid': processo_uuid, 'status_code': response.status_code, 'response': str(response.json())[:100]})
        return response  # type: ignore[no-any-return]
