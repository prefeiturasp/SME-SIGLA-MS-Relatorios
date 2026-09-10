"""Serviços para integração com API de candidatos."""

from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings
from requests import RequestException
from sigla_sdk.http.api_client import http_client

logger = logging.getLogger(__name__)


class CandidatosService:
    """Service para integração com API de candidatos."""

    base_url = settings.CANDIDATOS_API_URL.rstrip("/")
    timeout_seconds = 30
    _headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        settings.API_KEY_HEADER: settings.CANDIDATOS_API_KEY,
    }

    def buscar_habilitados(
        self,
        processo_uuid: str,
        codigo_cargo: list[str] | str | None = None,
        ordering: str = "ranking_escolha",
    ) -> requests.Response:
        """Busca habilitados.

        Args:
            processo_uuid: UUID do processo de convocação.
            codigo_cargo: Código numérico do cargo.
            ordering: Ordering.

        Returns:
            Resposta HTTP com o arquivo para download.
        """
        url = f"{self.base_url}/api/v1/habilitados/"
        params = {"processo_uuid": processo_uuid, "ordering": ordering}
        if codigo_cargo is not None:
            if isinstance(codigo_cargo, list):
                if len(codigo_cargo) > 1:
                    params["codigo_cargo__in"] = ",".join(
                        str(c) for c in codigo_cargo
                    )
                elif len(codigo_cargo) == 1:
                    params["codigo_cargo"] = str(codigo_cargo[0])
            else:
                codigo_cargo_param = str(codigo_cargo)
                if "," in codigo_cargo_param:
                    params["codigo_cargo__in"] = codigo_cargo_param
                else:
                    params["codigo_cargo"] = codigo_cargo_param
        logger.info(
            f"Buscando candidatos habilitados | method=GET url={url} "
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
                f"Erro ao buscar candidatos habilitados | "
                f"processo_uuid={processo_uuid} "
                f"codigo_cargo={params.get('codigo_cargo') or params.get('codigo_cargo__in')} "
                f"error={exc}"
            )
            raise
        logger.info(
            f"Candidatos habilitados buscados com sucesso | method=GET "
            f"url={url} headers={self._headers} "
            f"status_code={response.status_code} "
            f"response={str(response.json())[:100]}"
        )
        return response  # type: ignore[no-any-return]

    def buscar_habilitados_por_processos_e_classificacoes(
        self,
        processo_uuids: list[str] | str,
        classificacao: list[int] | list[str] | str | None = None,
        classificacao_nna: list[int] | list[str] | str | None = None,
        codigo_cargo: list[str] | str | None = None,
        ordering: str = "ranking_escolha",
    ) -> requests.Response:
        """Busca habilitados por processos e classificacoes.

        Args:
            processo_uuids: Processo uuids.
            classificacao: Classificacao.
            classificacao_nna: Classificacao nna.
            codigo_cargo: Código numérico do cargo.
            ordering: Ordering.

        Returns:
            Resposta HTTP com o arquivo para download.
        """
        url = f"{self.base_url}/api/v1/habilitados/"
        if isinstance(processo_uuids, list):
            processo_uuid_param = ",".join(processo_uuids)
        else:
            processo_uuid_param = processo_uuids
        params = {"ordering": ordering}
        if isinstance(processo_uuids, list):
            if len(processo_uuids) > 1:
                params["processo_uuid__in"] = ",".join(processo_uuids)
            else:
                params["processo_uuid"] = processo_uuids[0]
        elif "," in processo_uuid_param:
            params["processo_uuid__in"] = processo_uuid_param
        else:
            params["processo_uuid"] = processo_uuid_param
        if classificacao is not None:
            if isinstance(classificacao, list):
                classificacao_param = ",".join(str(c) for c in classificacao)
                if len(classificacao) > 1:
                    params["classificacao__in"] = classificacao_param
                else:
                    params["classificacao"] = classificacao_param
            else:
                classificacao_param = str(classificacao)
                if "," in classificacao_param:
                    params["classificacao__in"] = classificacao_param
                else:
                    params["classificacao"] = classificacao_param
        if classificacao_nna is not None:
            if isinstance(classificacao_nna, list):
                classificacao_nna_param = ",".join(
                    str(c) for c in classificacao_nna
                )
                if len(classificacao_nna) > 1:
                    params["classificacao_nna__in"] = classificacao_nna_param
                else:
                    params["classificacao_nna"] = classificacao_nna_param
            else:
                classificacao_nna_param = str(classificacao_nna)
                if "," in classificacao_nna_param:
                    params["classificacao_nna__in"] = classificacao_nna_param
                else:
                    params["classificacao_nna"] = classificacao_nna_param
        if codigo_cargo is not None:
            if isinstance(codigo_cargo, list):
                codigo_cargo_param = ",".join(str(c) for c in codigo_cargo)
                if len(codigo_cargo) > 1:
                    params["codigo_cargo__in"] = codigo_cargo_param
                else:
                    params["codigo_cargo"] = codigo_cargo_param
            else:
                codigo_cargo_param = str(codigo_cargo)
                if "," in codigo_cargo_param:
                    params["codigo_cargo__in"] = codigo_cargo_param
                else:
                    params["codigo_cargo"] = codigo_cargo_param
        logger.info(
            f"Buscando candidatos habilitados por processos e classificações | "
            f"method=GET url={url} headers={self._headers} params={params}"
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
                f"Erro ao buscar candidatos habilitados | "
                f"processo_uuids={processo_uuid_param} "
                f"classificacao={params.get('classificacao')} "
                f"classificacao_nna={params.get('classificacao_nna')} "
                f"codigo_cargo={params.get('codigo_cargo')} error={exc}"
            )
            raise
        logger.info(
            f"Candidatos habilitados buscados com sucesso | method=GET "
            f"url={url} headers={self._headers} params={params} "
            f"status_code={response.status_code} "
            f"response={str(response.json())[:100]}"
        )
        return response  # type: ignore[no-any-return]

    def buscar_por_uuids(
        self, uuids: list[str], order_by: str = "ranking_escolha"
    ) -> requests.Response:
        """Busca por uuids.

        Args:
            uuids: Uuids.
            order_by: Order by.

        Returns:
            Resposta HTTP com o arquivo para download.
        """
        url = f"{self.base_url}/api/v1/habilitados/buscar-por-uuids/"
        params = {"order_by": order_by}
        payload = {"uuids": uuids}
        logger.info(
            f"Buscando candidatos por UUIDs | method=POST params={params} "
            f"payload={payload} url={url} headers={self._headers}"
        )
        try:
            response = http_client.post(
                url,
                params=params,
                json=payload,
                headers=self._headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except RequestException as exc:
            logger.error(
                f"Erro ao buscar candidatos por UUIDs | "
                f"total_uuids={len(uuids)} order_by={order_by} error={exc}"
            )
            raise
        logger.info(
            f"Candidatos buscados por UUIDs com sucesso | method=POST "
            f"url={url} headers={self._headers} params={params} "
            f"payload={payload} status_code={response.status_code} "
            f"response={str(response.json())[:100]}"
        )
        return response  # type: ignore[no-any-return]

    def buscar_extracao_dados(
        self,
        concurso_uuid: str | None = None,
        filtros: list[dict] | None = None,
    ) -> dict:
        """
        Busca dados de extração de habilitados e convocados agrupados por ano/processo.

        Endpoint esperado do ms-candidatos:
            POST /api/v1/habilitados/extracao-dados/

        Args:
            concurso_uuid: UUID do concurso
            filtros: Lista de filtros com ano e processo_uuids

        Returns:
            Dados da API com extração

        Raises:
            RequestException: Em caso de erro na requisição
        """
        url = f"{self.base_url}/api/v1/habilitados/extracao-dados/"
        payload: dict[str, Any] = {}
        if concurso_uuid is not None:
            payload["concurso_uuid"] = concurso_uuid
        if filtros is not None:
            payload["filtros"] = filtros
        logger.info(
            f"Buscando totais de habilitados por processo e ano | "
            f"method=POST url={url} headers={self._headers} payload={payload}"
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
                f"Erro ao buscar totais de habilitados por processo e ano | "
                f"concurso_uuid={concurso_uuid} error={exc}"
            )
            raise

        logger.info(
            f"Totais de habilitados por processo e ano buscados com sucesso | "
            f"method=POST url={url} headers={self._headers} "
            f"payload={payload} status_code={response.status_code} "
            f"response={str(response.json())[:100]}"
        )
        return response.json()  # type: ignore[no-any-return]

    def buscar_candidatos_por_agendas(
        self,
        agendas_response: requests.Response,
        order_by: str = "ranking_escolha",
    ) -> dict:
        """Busca candidatos por agendas.

        Args:
            agendas_response: Agendas response.
            order_by: Order by.

        Returns:
            Dicionário com os dados processados.
        """
        try:
            agendas_data = agendas_response.json()
            if isinstance(agendas_data, dict) and "results" in agendas_data:
                agendas = agendas_data["results"]
            elif isinstance(agendas_data, list):
                agendas = agendas_data
            else:
                agendas = []
            logger.info(
                f"Processando {len(agendas)} agendas para buscar candidatos"
            )
            resultado = {"agendas": []}  # type: ignore[var-annotated]
            for agenda in agendas:
                candidatos_uuids = agenda.get("candidatos_uuids", [])
                if not candidatos_uuids:
                    logger.warning(
                        f"Agenda {agenda.get('uuid', 'desconhecido')} "
                        f"não possui candidatos_uuids"
                    )
                    resultado["agendas"].append(
                        {"agenda": agenda, "candidatos": []}
                    )
                    continue
                try:
                    response_candidatos = self.buscar_por_uuids(
                        uuids=candidatos_uuids, order_by=order_by
                    )
                    candidatos_data = response_candidatos.json()
                    if (
                        isinstance(candidatos_data, dict)
                        and "results" in candidatos_data
                    ):
                        candidatos = candidatos_data["results"]
                    elif isinstance(candidatos_data, list):
                        candidatos = candidatos_data
                    else:
                        candidatos = []
                    logger.info(
                        f"Encontrados {len(candidatos)} candidatos para agenda "
                        f"{agenda.get('uuid', 'desconhecido')} "
                        f"(de {len(candidatos_uuids)} UUIDs)"
                    )
                    resultado["agendas"].append(
                        {"agenda": agenda, "candidatos": candidatos}
                    )
                except RequestException as exc:
                    logger.error(
                        f"Erro ao buscar candidatos para agenda "
                        f"{agenda.get('uuid', 'desconhecido')}: {exc}"
                    )
                    resultado["agendas"].append(
                        {"agenda": agenda, "candidatos": [], "erro": str(exc)}
                    )
            logger.info(
                f"Processamento concluído: "
                f"{len(resultado['agendas'])} agendas processadas"
            )
            return resultado
        except Exception as exc:
            logger.error(
                f"Erro ao processar agendas e buscar candidatos: {exc}"
            )
            raise

    def buscar_concurso_candidatos_por_processo(
        self, processo_uuid: str
    ) -> requests.Response:
        """Busca concurso candidatos por processo.

        Args:
            processo_uuid: UUID do processo de convocação.

        Returns:
            Resposta HTTP com o arquivo para download.
        """
        url = f"{self.base_url}/api/v1/habilitados/"
        params = {"processo_uuid": processo_uuid, "page_size": 10000}
        logger.info(
            f"Buscando ConcursoCandidato | method=GET url={url} "
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
            logger.error(f"Erro ao buscar ConcursoCandidato: {exc}")
            raise
        logger.info(
            f"ConcursoCandidato encontrado | method=GET url={url} "
            f"headers={self._headers} params={params} "
            f"status_code={response.status_code} "
            f"response={str(response.json())[:100]}"
        )
        return response  # type: ignore[no-any-return]

    def buscar_reclassificados_por_concurso(
        self, concurso_uuid: str, processo_uuid: str
    ) -> requests.Response:
        """Busca reclassificados por concurso.

        Args:
            concurso_uuid: UUID do concurso relacionado.
            processo_uuid: UUID do processo de convocação.

        Returns:
            Resposta HTTP com o arquivo para download.
        """
        url = f"{self.base_url}/api/v1/reclassificados/"
        params = {
            "concurso_uuid": concurso_uuid,
            "processo_uuid": processo_uuid,
        }
        logger.info(
            f"Buscando reclassificados | method=GET url={url} "
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
            logger.error(
                f"Erro ao buscar reclassificados | "
                f"concurso_uuid={concurso_uuid} error={exc}"
            )
            raise
        logger.info(
            f"Reclassificados encontrados | method=GET url={url} "
            f"headers={self._headers} params={params} "
            f"status_code={response.status_code} "
            f"response={str(response.json())[:100]}"
        )
        return response  # type: ignore[no-any-return]

    def buscar_eliminados_por_concurso(
        self,
        concurso_uuid: str,
        processo_uuid: str,
        classificacao_max: int,
        classificacao_min: int,
    ) -> requests.Response:
        """Busca eliminados por concurso.

        Args:
            concurso_uuid: UUID do concurso relacionado.
            processo_uuid: UUID do processo de convocação.
            classificacao_max: Classificacao max.
            classificacao_min: Classificacao min.

        Returns:
            Resposta HTTP com o arquivo para download.
        """
        url = f"{self.base_url}/api/v1/eliminados/"
        params = {
            "concurso_uuid": concurso_uuid,
            "processo_uuid": processo_uuid,
            "classificacao_max": classificacao_max,
            "classificacao_min": classificacao_min,
        }
        logger.info(
            f"Buscando eliminados | method=GET url={url} "
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
            logger.error(
                f"Erro ao buscar eliminados | concurso_uuid={concurso_uuid} "
                f"processo_uuid={processo_uuid} "
                f"classificacao_max={classificacao_max} "
                f"classificacao_min={classificacao_min} error={exc}"
            )
            raise
        logger.info(
            f"Eliminados encontrados | method=GET url={url} "
            f"headers={self._headers} params={params} "
            f"status_code={response.status_code} "
            f"response={str(response.json())[:100]}"
        )
        return response  # type: ignore[no-any-return]
