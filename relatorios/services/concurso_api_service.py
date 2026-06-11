"""
Serviços para integração com API de concursos.
"""

import logging

import requests
from requests import RequestException
from sigla_sdk.context import get_correlation_id
from sigla_sdk.http.api_client import http_client

logger = logging.getLogger(__name__)


class ConcursoService:
    """Service para integração com API de concursos."""

    def __init__(
        self, base_url: str = "https://example.com", timeout_seconds: int = 30
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._default_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def buscar_extracao_dados(
        self,
        concurso_uuid: str | None = None,
        ano: int | None = None,
    ) -> dict:
        """
        Busca dados de extração do concurso.

        Endpoint esperado do ms-concursos:
            GET /api/v1/extracao-dados/

        Args:
            concurso_uuid: UUID do concurso (opcional)
            ano: Ano de referência YYYY (opcional)

        Returns:
            Dados da API com extração do concurso

        Raises:
            RequestException: Em caso de erro na requisição
        """
        url = f"{self.base_url}/api/v1/extracao-dados/"
        payload = {}
        if concurso_uuid is not None:
            payload["concurso_uuid"] = concurso_uuid
        if ano is not None:
            payload["ano"] = ano
        logger.info(
            "Buscando extração de dados em concursos",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
                "url": url,
                "headers": self._default_headers,
                "payload": payload,
            },
        )
        try:
            response = http_client.post(
                url,
                json=payload,
                headers=self._default_headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except RequestException as exc:
            logger.error(
                "Erro ao buscar extração de dados em concursos "
                "(concurso_uuid=%s, ano=%s): %s",
                concurso_uuid,
                ano,
                exc,
            )
            raise

        logger.info(
            "Extração de dados em concursos buscada com sucesso",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
                "url": url,
                "headers": self._default_headers,
                "payload": payload,
                "status_code": response.status_code,
                "response": str(response.json())[:100],
            },
        )
        return response.json()
