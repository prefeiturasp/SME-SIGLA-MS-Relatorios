"""Serviços para integração com API de agendas."""

from __future__ import annotations

import logging

import requests
from requests import RequestException
from sigla_sdk.context import get_correlation_id
from sigla_sdk.http.api_client import http_client

logger = logging.getLogger(__name__)


class AgendasService:
    """Service para integração com API de agendas."""

    def __init__(
        self, base_url: str = "https://example.com", timeout_seconds: int = 30
    ) -> None:
        """'123456789-=.

        Args:
            self: Instância do objeto.
            base_url: URL base da API de agendas.
            timeout_seconds: Timeout em segundos para as requisições.

        Raises:
            Nenhuma exceção específica documentada.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._default_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def buscar_agendas(
        self,
        processo_convocacao_uuid: str,
        page: int = 1,
        page_size: int = 100,
    ) -> requests.Response:
        """Busca agendas por processo_convocacao_uuid com paginação.

        Args:
            self: Instância do objeto.
            processo_convocacao_uuid: UUID do processo de convocação.
            page: Número da página (padrão: 1).
            page_size: Tamanho da página (padrão: 100).

        Returns:
            Resposta HTTP com o resultado da operação.

        Raises:
            Nenhuma exceção específica documentada.
        """
        url = f"{self.base_url}/api/v1/agendas/"
        params = {
            "page": page,
            "page_size": page_size,
            "processo_convocacao_uuid": processo_convocacao_uuid,
        }
        logger.info(
            "Buscando agendas",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
                "url": url,
                "params": params,
                "headers": self._default_headers,
            },
        )
        try:
            response = http_client.get(
                url,
                params=params,
                headers=self._default_headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except RequestException as exc:
            logger.error(
                "Erro ao buscar agendas (processo_convocacao_uuid=%s): %s",
                processo_convocacao_uuid,
                exc,
            )
            raise
        logger.info(
            "Agendas buscadas com sucesso",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
                "url": url,
                "params": params,
                "headers": self._default_headers,
            },
        )
        return response  # type: ignore[no-any-return]

    def buscar_agenda_por_uuid(self, agenda_uuid: str) -> requests.Response:
        """Busca uma agenda específica pelo UUID.

        Args:
            self: Instância do objeto.
            agenda_uuid: UUID da agenda.

        Returns:
            Resposta HTTP com o resultado da operação.

        Raises:
            Nenhuma exceção específica documentada.
        """
        url = f"{self.base_url}/api/v1/agendas/{agenda_uuid}/"
        logger.info(
            "Buscando agenda por UUID",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
                "url": url,
                "headers": self._default_headers,
            },
        )
        try:
            response = http_client.get(
                url,
                headers=self._default_headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except RequestException as exc:
            logger.error(
                "Erro ao buscar agenda por UUID",
                extra={
                    "correlation_id": get_correlation_id(),
                    "method": "GET",
                    "url": url,
                    "headers": self._default_headers,
                    "error": str(exc),
                },
            )
            raise
        logger.info(
            "Agenda buscada com sucesso",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
                "url": url,
                "headers": self._default_headers,
            },
        )
        return response  # type: ignore[no-any-return]
