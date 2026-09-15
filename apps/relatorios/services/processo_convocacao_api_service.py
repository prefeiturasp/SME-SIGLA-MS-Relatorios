"""Serviços para integração com API de processos de convocação."""

from __future__ import annotations

import logging

import requests
from django.conf import settings
from requests import RequestException
from sigla_sdk.http.api_client import http_client

logger = logging.getLogger(__name__)


class ProcessoConvocacaoService:
    """Service para integração com API de processos de convocação."""

    base_url = settings.CONVOCACAO_API_URL.rstrip("/")
    timeout_seconds = 30
    _headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        settings.API_KEY_HEADER: settings.CONVOCACAO_API_KEY,
    }

    def buscar_processo_convocacao(
        self, processo_uuid: str
    ) -> requests.Response:
        """Busca processo convocacao.

        Args:
            processo_uuid: UUID do processo de convocação.

        Returns:
            Resposta HTTP com o arquivo para download.
        """
        url = f"{self.base_url}/api/v1/processos-convocacao/{processo_uuid}/"
        logger.info(
            f"Buscando processo de convocação | method=GET url={url} "
            f"headers={self._headers} processo_uuid={processo_uuid}"
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
                f"Erro ao buscar processo de convocação | "
                f"processo_uuid={processo_uuid} error={exc}"
            )
            raise
        logger.info(
            f"Processo de convocação encontrado | method=GET url={url} "
            f"headers={self._headers} processo_uuid={processo_uuid} "
            f"status_code={response.status_code} "
            f"response={str(response.json())[:100]}"
        )
        return response  # type: ignore[no-any-return]

    def buscar_processos_por_concurso(
        self, concurso_uuid: str
    ) -> requests.Response:
        """Busca processos por concurso.

        Args:
            concurso_uuid: UUID do concurso relacionado.

        Returns:
            Resposta HTTP com o arquivo para download.
        """
        url = f"{self.base_url}/api/v1/processos-convocacao/"
        params = {"concurso_uuid": concurso_uuid}
        logger.info(
            f"Buscando processos de convocação por concurso | method=GET "
            f"url={url} headers={self._headers} params={params}"
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
                f"Erro ao buscar processos de convocação | "
                f"concurso_uuid={concurso_uuid} error={exc}"
            )
            raise
        logger.info(
            f"Processos de convocação por concursos encontrados | "
            f"method=GET url={url} headers={self._headers} params={params} "
            f"status_code={response.status_code} "
            f"response={str(response.json())[:100]}"
        )
        return response  # type: ignore[no-any-return]

    def separar_processos_por_principal(
        self, processo_data: dict
    ) -> tuple[str, list[str]]:
        """Separa processo principal e demais do mesmo concurso.

        Args:
            processo_data: Processo data.

        Returns:
            Tupla com os objetos criados ou atualizados.

        Raises:
            ValueError: Se os dados informados forem inválidos.
        """
        logger.info(
            f"Separando processos por principal | processo_data={processo_data}"
        )
        concurso_uuid = processo_data.get("concurso_uuid")
        if not concurso_uuid:
            raise ValueError(
                f"Processo {processo_data.get('uuid')} não possui concurso_uuid"  # noqa: E501
            )
        response_processos = self.buscar_processos_por_concurso(concurso_uuid)
        processos_data = response_processos.json()
        if isinstance(processos_data, dict) and "results" in processos_data:
            processos_list = processos_data["results"]
        elif isinstance(processos_data, list):
            processos_list = processos_data
        else:
            processos_list = [processos_data]
        outros_processos_uuid = []
        for processo in processos_list:
            processo_uuid = processo.get("uuid") or processo.get("id")
            if processo_uuid and processo_uuid != processo_data.get("uuid"):
                outros_processos_uuid.append(processo_uuid)
        logger.info(
            f"Processos por principal separados | "
            f"processo_data={processo_data} processos_list={processos_list} "
            f"outros_processos_uuid={outros_processos_uuid}"
        )
        return (processo_data.get("uuid"), outros_processos_uuid)  # type: ignore[return-value]
