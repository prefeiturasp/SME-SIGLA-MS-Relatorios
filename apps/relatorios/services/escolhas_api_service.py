"""Serviços para integração com API de escolhas."""

from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings
from requests import RequestException
from sigla_sdk.http.api_client import http_client

logger = logging.getLogger(__name__)


class EscolhasService:
    """Serviço para operações de escolhas."""

    base_url = settings.ESCOLHAS_API_URL.rstrip("/")
    timeout_seconds = 30
    _headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        settings.API_KEY_HEADER: settings.ESCOLHAS_API_KEY,
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
            f"Buscando vagas de escolas | method=GET "
            f"processo_uuid={processo_uuid} url={url} "
            f"headers={self._headers} params={params}"
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
            logger.error(f"Erro ao buscar vagas de escolas | error={exc}")
            raise
        logger.info(
            f"Vagas de escolas encontradas | method=GET "
            f"processo_uuid={processo_uuid} url={url} "
            f"headers={self._headers} params={params} "
            f"status_code={response.status_code} "
            f"response={str(response.json())[:100]}"
        )
        return response  # type: ignore[no-any-return]

    def buscar_escolhas_por_candidatos(
        self, candidato_uuids: list, situacao: str | None = "nao-escolha"
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
            f"Buscando escolhas por candidatos | method=POST "
            f"candidato_uuids={candidato_uuids} situacao={situacao} "
            f"url={url} headers={self._headers}"
        )
        try:
            response = http_client.post(
                url,
                json=data,
                headers=self._headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except RequestException as exc:
            logger.error(f"Erro ao buscar escolhas | error={exc}")
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
            f"Escolhas buscadas com sucesso | "
            f"candidatos={len(candidato_uuids)} situacao={situacao} "
            f"filtradas={len(escolhas_filtradas)}"
        )
        return escolhas_filtradas

    def buscar_extracao_dados(
        self,
        concurso_uuid: str | None = None,
        filtros: list[dict] | None = None,
    ) -> dict:
        """
        Busca dados agregados de extração por concurso e processos/ano.

        Endpoint esperado do ms-escolhas:
            POST /api/v1/escolhas/extracao-dados/

        Args:
            concurso_uuid: UUID do concurso (opcional)
            filtros: Lista de filtros com ano e processo_uuids (opcional)

        Returns:
            Dados da API com extração

        Raises:
            RequestException: Em caso de erro na requisição
        """
        url = f"{self.base_url}/api/v1/extracao-dados/"
        payload: dict[str, Any] = {}
        if concurso_uuid is not None:
            payload["concurso_uuid"] = concurso_uuid
        if filtros is not None:
            payload["filtros"] = filtros
        logger.info(
            f"Buscando extração de dados em escolhas | method=POST "
            f"url={url} headers={self._headers} payload={payload}"
        )
        try:
            response = http_client.post(
                url,
                json=payload,
                headers=self._headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except RequestException as exc:
            logger.error(
                f"Erro ao buscar extração de dados em escolhas | "
                f"concurso_uuid={concurso_uuid} error={exc}"
            )
            raise

        logger.info(
            f"Extração de dados em escolhas buscada com sucesso | "
            f"method=POST url={url} headers={self._headers} "
            f"payload={payload} status_code={response.status_code} "
            f"response={str(response.json())[:100]}"
        )
        return response.json()  # type: ignore[no-any-return]
