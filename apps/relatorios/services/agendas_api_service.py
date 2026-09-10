"""Serviços para integração com API de agendas."""

from __future__ import annotations

import logging

import requests
from django.conf import settings
from requests import RequestException
from sigla_sdk.http.api_client import http_client

logger = logging.getLogger(__name__)


class AgendasService:
    """Service para integração com API de agendas."""

    base_url = settings.AGENDAS_API_URL.rstrip("/")
    timeout_seconds = 30
    _headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        settings.API_KEY_HEADER: settings.AGENDAS_API_KEY,
    }

    def buscar_agendas(
        self,
        processo_convocacao_uuid: str,
        page: int = 1,
        page_size: int = 100,
    ) -> requests.Response:
        """Busca agendas.

        Args:
            processo_convocacao_uuid: UUID de processo convocacao.
            page: Page.
            page_size: Page size.

        Returns:
            Resposta HTTP com o arquivo para download.
        """
        url = f"{self.base_url}/api/v1/agendas/"
        params = {
            "page": page,
            "page_size": page_size,
            "processo_convocacao_uuid": processo_convocacao_uuid,
        }
        logger.info(
            f"Buscando agendas | method=GET url={url} params={params} "
            f"headers={self._headers}"
        )
        try:
            response = http_client.get(
                url,
                params=params,
                headers=self._headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except RequestException as exc:
            logger.error(
                f"Erro ao buscar agendas | "
                f"processo_convocacao_uuid={processo_convocacao_uuid} "
                f"error={exc}"
            )
            raise
        logger.info(
            f"Agendas buscadas com sucesso | method=GET url={url} "
            f"params={params} headers={self._headers}"
        )
        return response  # type: ignore[no-any-return]

    def buscar_agenda_por_uuid(self, agenda_uuid: str) -> requests.Response:
        """Busca agenda por uuid.

        Args:
            agenda_uuid: UUID de agenda.

        Returns:
            Resposta HTTP com o arquivo para download.
        """
        url = f"{self.base_url}/api/v1/agendas/{agenda_uuid}/"
        logger.info(
            f"Buscando agenda por UUID | method=GET url={url} "
            f"headers={self._headers}"
        )
        try:
            response = http_client.get(
                url,
                headers=self._headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except RequestException as exc:
            logger.error(
                f"Erro ao buscar agenda por UUID | method=GET url={url} "
                f"headers={self._headers} error={exc}"
            )
            raise
        logger.info(
            f"Agenda buscada com sucesso | method=GET url={url} "
            f"headers={self._headers}"
        )
        return response  # type: ignore[no-any-return]
