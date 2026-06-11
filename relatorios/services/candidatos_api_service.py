"""
Serviços para integração com API de candidatos.
"""

import logging

import requests
from requests import RequestException
from sigla_sdk.context import get_correlation_id
from sigla_sdk.http.api_client import http_client

logger = logging.getLogger(__name__)


class CandidatosService:
    """
    Service para integração com API de candidatos.
    """

    def __init__(
        self, base_url: str = "https://example.com", timeout_seconds: int = 30
    ):
        """
        Inicializa o serviço de candidatos.

        Args:
            base_url: URL base da API de candidatos
            timeout_seconds: Timeout em segundos para as requisições
        """
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._default_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def buscar_habilitados(
        self,
        processo_uuid: str,
        codigo_cargo: list[str] | str | None = None,
        ordering: str = "ranking_escolha",
    ) -> requests.Response:
        """
        Busca candidatos habilitados por processo_uuid, ordenados por
        ranking_escolha.

        Args:
            processo_uuid: UUID do processo de convocação
            codigo_cargo: Código(s) de cargo para filtragem (opcional)
            ordering: Campo para ordenação (padrão: 'ranking_escolha')

        Returns:
            Response da API com os candidatos habilitados

        Raises:
            RequestException: Em caso de erro na requisição
        """
        url = f"{self.base_url}/api/v1/habilitados/"

        params = {
            "processo_uuid": processo_uuid,
            "ordering": ordering,
        }
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
            "Buscando candidatos habilitados",
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
                params=params,
                headers=self._default_headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()

        except RequestException as exc:
            logger.error(
                "Erro ao buscar candidatos habilitados (processo_uuid=%s, codigo_cargo=%s): %s",  # noqa: E501
                processo_uuid,
                params.get("codigo_cargo") or params.get("codigo_cargo__in"),
                exc,
            )
            raise

        logger.info(
            "Candidatos habilitados buscados com sucesso",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
                "url": url,
                "headers": self._default_headers,
                "status_code": response.status_code,
                "response": str(response.json())[:100],
            },
        )
        return response

    def buscar_habilitados_por_processos_e_classificacoes(
        self,
        processo_uuids: list[str] | str,
        classificacao: list[int] | list[str] | str | None = None,
        classificacao_nna: list[int] | list[str] | str | None = None,
        codigo_cargo: list[str] | str | None = None,
        ordering: str = "ranking_escolha",
    ) -> requests.Response:
        """
        Busca candidatos habilitados em múltiplos processos com classificações
        específicas.
        Suporta filtros por classificacao e/ou classificacao_nna de forma
        flexível.

        Args:
            processo_uuids: Lista de UUIDs dos processos ou string com UUIDs
            separados por vírgula
            classificacao: Lista de classificações ou string com classificações
            separadas por vírgula (opcional)
            classificacao_nna: Lista de classificações NNA ou string com
            classificações separadas por vírgula (opcional)
            codigo_cargo: Lista de códigos de cargo ou string com códigos
            separados por vírgula (opcional)
            ordering: Campo para ordenação (padrão: 'ranking_escolha')

        Returns:
            Response da API com os candidatos habilitados

        Raises:
            RequestException: Em caso de erro na requisição
        """
        url = f"{self.base_url}/api/v1/habilitados/"

        # Normaliza processo_uuids para string separada por vírgula
        if isinstance(processo_uuids, list):
            processo_uuid_param = ",".join(processo_uuids)
        else:
            processo_uuid_param = processo_uuids

        params = {
            "ordering": ordering,
        }

        # Adiciona processo_uuid - django-filter aceita vírgulas com sufixo __in  # noqa: E501
        # Para múltiplos valores, usa o formato: processo_uuid__in=uuid1,uuid2
        if isinstance(processo_uuids, list):
            if len(processo_uuids) > 1:
                params["processo_uuid__in"] = ",".join(processo_uuids)
            else:
                params["processo_uuid"] = processo_uuids[0]
        else:
            # String: verifica se tem vírgula (múltiplos valores)
            if "," in processo_uuid_param:
                params["processo_uuid__in"] = processo_uuid_param
            else:
                params["processo_uuid"] = processo_uuid_param

        # Adiciona classificacao se fornecido
        # django-filter aceita vírgulas: classificacao__in=1,2,3
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

        # Adiciona classificacao_nna se fornecido
        # django-filter aceita vírgulas: classificacao_nna__in=1,2,3
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

        # Adiciona codigo_cargo se fornecido
        # django-filter aceita vírgulas: codigo_cargo__in=cod1,cod2
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
            "Buscando candidatos habilitados por processos e classificações",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
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
            logger.error(
                "Erro ao buscar candidatos habilitados (processo_uuids=%s, classificacao=%s, classificacao_nna=%s, codigo_cargo=%s): %s",  # noqa: E501
                processo_uuid_param,
                params.get("classificacao"),
                params.get("classificacao_nna"),
                params.get("codigo_cargo"),
                exc,
            )
            raise
        logger.info(
            "Candidatos habilitados buscados com sucesso",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
                "url": url,
                "headers": self._default_headers,
                "params": params,
                "status_code": response.status_code,
                "response": str(response.json())[:100],
            },
        )
        return response

    def buscar_por_uuids(
        self, uuids: list[str], order_by: str = "ranking_escolha"
    ) -> requests.Response:
        """
        Busca candidatos habilitados por uma lista de UUIDs usando método POST.

        Args:
            uuids: Lista de UUIDs dos candidatos
            order_by: Campo para ordenação (padrão: 'ranking_escolha')

        Returns:
            Response da API com os candidatos habilitados

        Raises:
            RequestException: Em caso de erro na requisição
        """
        url = f"{self.base_url}/api/v1/habilitados/buscar-por-uuids/"

        params = {
            "order_by": order_by,
        }

        payload = {"uuids": uuids}
        logger.info(
            "Buscando candidatos por UUIDs",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "POST",
                "params": params,
                "payload": payload,
                "url": url,
                "headers": self._default_headers,
            },
        )

        try:
            response = http_client.post(
                url,
                params=params,
                json=payload,
                headers=self._default_headers,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except RequestException as exc:
            logger.error(
                "Erro ao buscar candidatos por UUIDs (total_uuids=%d, order_by=%s): %s",  # noqa: E501
                len(uuids),
                order_by,
                exc,
            )
            raise
        logger.info(
            "Candidatos buscados por UUIDs com sucesso",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "POST",
                "url": url,
                "headers": self._default_headers,
                "params": params,
                "payload": payload,
                "status_code": response.status_code,
                "response": str(response.json())[:100],
            },
        )
        return response

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
        payload = {}
        if concurso_uuid is not None:
            payload["concurso_uuid"] = concurso_uuid
        if filtros is not None:
            payload["filtros"] = filtros
        logger.info(
            "Buscando totais de habilitados por processo e ano",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "POST",
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
                "Erro ao buscar totais de habilitados por processo e ano "
                "(concurso_uuid=%s): %s",
                concurso_uuid,
                exc,
            )
            raise

        logger.info(
            "Totais de habilitados por processo e ano buscados com sucesso",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "POST",
                "url": url,
                "headers": self._default_headers,
                "payload": payload,
                "status_code": response.status_code,
                "response": str(response.json())[:100],
            },
        )
        return response.json()

    def buscar_candidatos_por_agendas(
        self,
        agendas_response: requests.Response,
        order_by: str = "ranking_escolha",
    ) -> dict:
        """
        Itera sobre as agendas retornadas e busca candidatos para cada agenda
        usando os candidatos_uuids de cada uma.

        Args:
            agendas_response: Response da API de agendas (deve conter 'results'
            com lista de agendas)
            order_by: Campo para ordenação (padrão: 'ranking_escolha')

        Returns:
            Dicionário com agendas e seus respectivos candidatos:
            {
                'agendas': [
                    {
                        'agenda': {...},  # Dados da agenda original
                        'candidatos': [...]  # Lista de candidatos encontrados
                    },
                    ...
                ]
            }

        Raises:
            RequestException: Em caso de erro nas requisições
        """
        try:
            agendas_data = agendas_response.json()

            # Extrair lista de agendas (pode estar em 'results' ou ser uma lista direta)  # noqa: E501
            if isinstance(agendas_data, dict) and "results" in agendas_data:
                agendas = agendas_data["results"]
            elif isinstance(agendas_data, list):
                agendas = agendas_data
            else:
                agendas = []

            logger.info(
                "Processando %d agendas para buscar candidatos", len(agendas)
            )

            resultado = {"agendas": []}

            for agenda in agendas:
                candidatos_uuids = agenda.get("candidatos_uuids", [])

                if not candidatos_uuids:
                    logger.warning(
                        "Agenda %s não possui candidatos_uuids",
                        agenda.get("uuid", "desconhecido"),
                    )
                    resultado["agendas"].append(
                        {"agenda": agenda, "candidatos": []}
                    )
                    continue

                try:
                    # Buscar candidatos usando os UUIDs da agenda
                    response_candidatos = self.buscar_por_uuids(
                        uuids=candidatos_uuids, order_by=order_by
                    )

                    candidatos_data = response_candidatos.json()

                    # Extrair lista de candidatos (pode ser uma lista direta ou um objeto com 'results')  # noqa: E501
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
                        "Encontrados %d candidatos para agenda %s (de %d UUIDs)",  # noqa: E501
                        len(candidatos),
                        agenda.get("uuid", "desconhecido"),
                        len(candidatos_uuids),
                    )

                    resultado["agendas"].append(
                        {"agenda": agenda, "candidatos": candidatos}
                    )

                except RequestException as exc:
                    logger.error(
                        "Erro ao buscar candidatos para agenda %s: %s",
                        agenda.get("uuid", "desconhecido"),
                        exc,
                    )
                    # Adiciona a agenda mesmo com erro, mas sem candidatos
                    resultado["agendas"].append(
                        {"agenda": agenda, "candidatos": [], "erro": str(exc)}
                    )

            logger.info(
                "Processamento concluído: %d agendas processadas",
                len(resultado["agendas"]),
            )

            return resultado

        except Exception as exc:
            logger.error(
                "Erro ao processar agendas e buscar candidatos: %s", exc
            )
            raise

    def buscar_concurso_candidatos_por_processo(
        self, processo_uuid: str
    ) -> requests.Response:
        """
        Busca ConcursoCandidato por processo_uuid.
        Tenta usar o endpoint /api/v1/candidatos/ que pode retornar
        ConcursoCandidato
        através do relacionamento 'concursos'.

        Args:
            processo_uuid: UUID do processo de convocação

        Returns:
            Response da API com os dados (pode ser Candidato ou
            ConcursoCandidato)

        Raises:
            RequestException: Em caso de erro na requisição
        """
        # O endpoint /api/v1/candidatos/ pode retornar Candidato com relacionamento concursos  # noqa: E501
        # Ou pode ter uma lógica customizada que retorna ConcursoCandidato
        # Vamos tentar buscar e ver o que retorna
        url = f"{self.base_url}/api/v1/habilitados/"

        params = {
            "processo_uuid": processo_uuid,
            "page_size": 10000,
        }
        logger.info(
            "Buscando ConcursoCandidato",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
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
            logger.error("Erro ao buscar ConcursoCandidato: %s", exc)
            raise

        logger.info(
            "ConcursoCandidato encontrado",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
                "url": url,
                "headers": self._default_headers,
                "params": params,
                "status_code": response.status_code,
                "response": str(response.json())[:100],
            },
        )
        return response

    def buscar_reclassificados_por_concurso(
        self, concurso_uuid: str, processo_uuid: str
    ) -> requests.Response:
        """
        Busca candidatos reclassificados (de NNA/PCD -> GERAL) por
        concurso_uuid.
        Endpoint esperado do ms-candidatos:
            GET /api/v1/reclassificados/?concurso_uuid=<uuid>
        Retorna um dicionário com duas chaves: 'nna' e 'pcd'.
        """
        url = f"{self.base_url}/api/v1/reclassificados/"
        params = {
            "concurso_uuid": concurso_uuid,
            "processo_uuid": processo_uuid,
        }
        logger.info(
            "Buscando reclassificados",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
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
            logger.error(
                "Erro ao buscar reclassificados (concurso_uuid=%s): %s",
                concurso_uuid,
                exc,
            )
            raise
        logger.info(
            "Reclassificados encontrados",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
                "url": url,
                "headers": self._default_headers,
                "params": params,
                "status_code": response.status_code,
                "response": str(response.json())[:100],
            },
        )
        return response

    def buscar_eliminados_por_concurso(
        self,
        concurso_uuid: str,
        processo_uuid: str,
        classificacao_max: int,
        classificacao_min: int,
    ) -> requests.Response:
        """
        Busca candidatos eliminados por concurso_uuid e classificacao_max e
        classificacao_min.
        Endpoint esperado do ms-candidatos:
            GET
            /api/v1/eliminados/?concurso_uuid=<uuid>&classificacao_max=<int>&classificacao_min=<int>
        Retorna um dicionário separado por tipo de classificação:
        {
          "geral": [...],
          "nna": [...],
          "pcd": [...]
        }
        """
        url = f"{self.base_url}/api/v1/eliminados/"
        params = {
            "concurso_uuid": concurso_uuid,
            "processo_uuid": processo_uuid,
            "classificacao_max": classificacao_max,
            "classificacao_min": classificacao_min,
        }
        logger.info(
            "Buscando eliminados",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
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
            logger.error(
                "Erro ao buscar eliminados (concurso_uuid=%s, processo_uuid=%s, classificacao_max=%s, classificacao_min=%s): %s",  # noqa: E501
                concurso_uuid,
                processo_uuid,
                classificacao_max,
                classificacao_min,
                exc,
            )
            raise
        logger.info(
            "Eliminados encontrados",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
                "url": url,
                "headers": self._default_headers,
                "params": params,
                "status_code": response.status_code,
                "response": str(response.json())[:100],
            },
        )
        return response
