"""
Serviços para integração com API de processos de convocação.
"""
import logging
from typing import List, Tuple
import requests
from requests import RequestException
from sigla_sdk.context import get_correlation_id
from sigla_sdk.http.api_client import http_client
logger = logging.getLogger(__name__)


class ProcessoConvocacaoService:
    """
    Service para integração com API de processos de convocação.
    """
    
    def __init__(self, base_url: str = 'https://example.com', timeout_seconds: int = 30):
        """
        Inicializa o serviço de processos de convocação.
        
        Args:
            base_url: URL base da API de processos de convocação
            timeout_seconds: Timeout em segundos para as requisições
        """
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self._default_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def buscar_processo_convocacao(self, processo_uuid: str) -> requests.Response:
        """
        Busca um processo de convocação por UUID.
        Args:
            processo_uuid: UUID do processo de convocação
        Returns:
            Response da API com os dados do processo de convocação
        Raises:
            RequestException: Em caso de erro na requisição
        """
        url = f"{self.base_url}/api/v1/processos-convocacao/{processo_uuid}/"
        logger.info(
            'Buscando processo de convocação',
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
                "url": url,
                "headers": self._default_headers,
                "processo_uuid": processo_uuid,
            }
        )
        try:
            response = http_client.get(
                url,
                headers=self._default_headers,
                timeout=self.timeout_seconds
            )
            response.raise_for_status()
        except RequestException as exc:
            logger.error('Erro ao buscar processo de convocação (processo_uuid=%s): %s', processo_uuid, exc)
            raise

        logger.info('Processo de convocação encontrado', extra={
            "correlation_id": get_correlation_id(),
            "method": "GET",
            "url": url,
            "headers": self._default_headers,
            "processo_uuid": processo_uuid,
            "status_code": response.status_code,
            "response": str(response.json())[:100],
        })
        return response

    def buscar_processos_por_concurso(self, concurso_uuid: str) -> requests.Response:
        """
        Busca processos de convocação por concurso_uuid.
        Args:
            concurso_uuid: UUID do concurso
        Returns:
            Response da API com a lista de processos de convocação do concurso
        Raises:
            RequestException: Em caso de erro na requisição
        """
        url = f"{self.base_url}/api/v1/processos-convocacao/"
        params = {
            'concurso_uuid': concurso_uuid,
        }
        logger.info(
            'Buscando processos de convocação por concurso',
            extra={
                "correlation_id": get_correlation_id(),
                "method": "GET",
                "url": url,
                "headers": self._default_headers,
                "params": params,
            }
        )
        try:
            response = http_client.get(
                url,
                params=params,
                headers=self._default_headers,
                timeout=self.timeout_seconds
            )
            response.raise_for_status()
        except RequestException as exc:
            logger.error('Erro ao buscar processos de convocação (concurso_uuid=%s): %s', concurso_uuid, exc)
            raise

        logger.info('Processos de convocação por concursos encontrados', extra={
            "correlation_id": get_correlation_id(),
            "method": "GET",
            "url": url,
            "headers": self._default_headers,
            "params": params,
            "status_code": response.status_code,
            "response": str(response.json())[:100],
        })
        return response

    def separar_processos_por_principal(
        self, 
        processo_data: dict
    ) -> Tuple[str, List[str]]:
        """
        Busca o processo principal e outros processos do mesmo concurso,
        separando-os em duas variáveis.
        Args:
            processo_data: Dicionário com os dados do processo principal
        Returns:
            Tupla contendo:
            - processo_data.get('uuid'): UUID do processo principal
            - outros_processos_uuid: Lista de UUIDs dos outros processos (excluindo o principal)
        Raises:
            RequestException: Em caso de erro nas requisições
            ValueError: Se o processo principal não for encontrado ou não tiver concurso_uuid
        """
        logger.info(
            'Separando processos por principal',
            extra={
                "correlation_id": get_correlation_id(),
                "processo_data": processo_data,
            }
        )
        # 1. Obter o concurso_uuid do processo principal
        concurso_uuid = processo_data.get('concurso_uuid')
        if not concurso_uuid:
            raise ValueError(
                f'Processo {processo_data.get('uuid')} não possui concurso_uuid'
            )

        # 3. Buscar todos os processos do mesmo concurso
        response_processos = self.buscar_processos_por_concurso(concurso_uuid)
        processos_data = response_processos.json()

        # Extrair lista de processos (pode ser uma lista direta ou um objeto com 'results')
        if isinstance(processos_data, dict) and 'results' in processos_data:
            processos_list = processos_data['results']
        elif isinstance(processos_data, list):
            processos_list = processos_data
        else:
            processos_list = [processos_data]

        # 4. Separar processos: principal e outros
        outros_processos_uuid = []

        for processo in processos_list:
            processo_uuid = processo.get('uuid') or processo.get('id')
            if processo_uuid and processo_uuid != processo_data.get('uuid'):
                outros_processos_uuid.append(processo_uuid)

        logger.info(
            'Processos por principal separados',
            extra={
                "correlation_id": get_correlation_id(),
                "processo_data": processo_data,
                "processos_list": processos_list,
                "outros_processos_uuid": outros_processos_uuid,
            }
        )

        return processo_data.get('uuid'), outros_processos_uuid