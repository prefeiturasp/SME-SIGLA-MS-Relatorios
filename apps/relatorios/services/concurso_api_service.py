"""
Serviços para integração com API de concursos.
"""

import logging
from typing import Any

from django.conf import settings
from requests import RequestException
from sigla_sdk.http.api_client import http_client

logger = logging.getLogger(__name__)


class ConcursoService:
    """Service para integração com API de concursos."""

    base_url = settings.CONCURSOS_API_URL.rstrip("/")
    timeout_seconds = 30
    _headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        settings.API_KEY_HEADER: settings.CONCURSOS_API_KEY,
    }

    def buscar_extracao_dados(
        self,
        concurso_uuid: str | None = None,
        anos: list[int] | None = None,
    ) -> dict:
        """
        Busca dados de extração do concurso.

        Endpoint esperado do ms-concursos:
            POST /api/v1/extracao-dados/

        Args:
            concurso_uuid: UUID do concurso (opcional)
            anos: Anos de referência YYYY (opcional)

        Returns:
            Dados da API com extração do concurso

        Raises:
            RequestException: Em caso de erro na requisição
        """
        url = f"{self.base_url}/api/v1/extracao-dados/"
        payload: dict[str, Any] = {}
        if concurso_uuid is not None:
            payload["concurso_uuid"] = concurso_uuid
        if anos is not None:
            payload["anos"] = anos
        logger.info(
            f"Buscando extração de dados em concursos | method=POST "
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
                f"Erro ao buscar extração de dados em concursos | "
                f"concurso_uuid={concurso_uuid} anos={anos} error={exc}"
            )
            raise

        logger.info(
            f"Extração de dados em concursos buscada com sucesso | "
            f"method=POST url={url} headers={self._headers} "
            f"payload={payload} status_code={response.status_code} "
            f"response={str(response.json())[:100]}"
        )
        return response.json()  # type: ignore[no-any-return]
