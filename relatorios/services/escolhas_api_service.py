"""Serviços para integração com API de escolhas."""

from __future__ import annotations

import logging

import requests
from requests import RequestException
from sigla_sdk.context import get_correlation_id
from sigla_sdk.http.api_client import http_client

logger = logging.getLogger(__name__)


class EscolhasService:
    """Serviço para operações de escolhas."""

    def __init__(
        self, base_url: str = "https://example.com", timeout_seconds: int = 30
    ) -> None:
        """Inicializa a instância com os parâmetros informados.

        Args:
            base_url: URL base do serviço remoto.
            timeout_seconds: Tempo máximo de espera, em segundos.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._default_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def buscar_vagas_escolas(self, processo_uuid: str) -> requests.Response:
        """Busca vagas escolas.

        Args:
            processo_uuid: UUID do processo de convocação.

        Returns:
            Resposta HTTP com o arquivo para download.
        """
        url = f"{self.base_url}/api/v1/vagas-escolas/"
        params = {"processo_uuid": processo_uuid}
        logger.info(
            "Buscando vagas de escolas",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
                "processo_uuid": processo_uuid,
                "url": url,
                "headers": self._default_headers,
                "params": params,
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
            logger.error("Erro ao buscar vagas de escolas: %s", exc)
            raise
        logger.info(
            "Vagas de escolas encontradas",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
                "processo_uuid": processo_uuid,
                "url": url,
                "headers": self._default_headers,
                "params": params,
                "status_code": response.status_code,
                "response": str(response.json())[:100],
            },
        )
        return response  # type: ignore[no-any-return]

    def buscar_escolhas_por_candidatos(
        self, candidato_uuids: list, situacao: str = "nao-escolha"
    ) -> list:
        """Busca escolhas por candidatos.

        Args:
            candidato_uuids: UUIDs dos candidatos consultados.
            situacao: Situacao.

        Returns:
            Lista com os registros obtidos.
        """
        url = f"{self.base_url}/api/v1/escolhas/busca/"
        data = {"candidato_uuid": candidato_uuids}
        logger.info(
            "Buscando escolhas por candidatos",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "POST",
                "candidato_uuids": candidato_uuids,
                "situacao": situacao,
                "url": url,
                "headers": self._default_headers,
            },
        )
        try:
            response = http_client.post(
                url,
                json=data,
                headers=self._default_headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except RequestException as exc:
            logger.error("Erro ao buscar escolhas: %s", exc)
            raise
        escolhas_data = response.json()
        if isinstance(escolhas_data, list):
            escolhas = escolhas_data
        elif isinstance(escolhas_data, dict) and "results" in escolhas_data:
            escolhas = escolhas_data.get("results", [])
        else:
            escolhas = []
        if situacao is None:
            escolhas_filtradas = escolhas
        else:
            escolhas_filtradas = [
                e for e in escolhas if e.get("situacao") == situacao
            ]
        logger.info(
            "Escolhas buscadas com sucesso (candidatos=%d, situacao=%s, filtradas=%d)",
            len(candidato_uuids),
            situacao,
            len(escolhas_filtradas),
        )
        return escolhas_filtradas
