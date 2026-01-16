"""
Serviços para integração com API de agendas.
"""
import logging
from typing import Optional
import requests
from requests import RequestException

logger = logging.getLogger(__name__)


class AgendasService:
    """
    Service para integração com API de agendas.
    """

    def __init__(self, base_url: str = 'https://example.com', timeout_seconds: int = 30):
        print("AGENDAS_SERVICE")
        print('base_url', base_url)
        """'123456789-=
        Inicializa o serviço de agendas.

        Args:
            base_url: URL base da API de agendas
            timeout_seconds: Timeout em segundos para as requisições
        """
        print("AGENDAS_SERVICE __init__")
        print('base_url', base_url)
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self._default_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def buscar_agendas(
        self,
        processo_convocacao_uuid: str,
        page: int = 1,
        page_size: int = 100
    ) -> requests.Response:
        """
        Busca agendas por processo_convocacao_uuid com paginação.

        Args:
            processo_convocacao_uuid: UUID do processo de convocação
            page: Número da página (padrão: 1)
            page_size: Tamanho da página (padrão: 100)

        Returns:
            Response da API com as agendas

        Raises:
            RequestException: Em caso de erro na requisição
        """
        url = f"{self.base_url}/api/v1/agendas/"

        params = {
            'page': page,
            'page_size': page_size,
            'processo_convocacao_uuid': processo_convocacao_uuid,
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=self._default_headers,
                timeout=self.timeout_seconds
            )
            response.raise_for_status()
            logger.info(
                'Agendas buscadas com sucesso (processo_convocacao_uuid=%s, page=%d, page_size=%d)',
                processo_convocacao_uuid,
                page,
                page_size
            )
            return response
        except RequestException as exc:
            logger.error(
                'Erro ao buscar agendas (processo_convocacao_uuid=%s): %s',
                processo_convocacao_uuid,
                exc
            )
            raise

    def buscar_agenda_por_uuid(
        self,
        agenda_uuid: str
    ) -> requests.Response:
        """
        Busca uma agenda específica pelo UUID.

        Args:
            agenda_uuid: UUID da agenda

        Returns:
            Response da API com os dados da agenda

        Raises:
            RequestException: Em caso de erro na requisição
        """
        url = f"{self.base_url}/api/v1/agendas/{agenda_uuid}/"
        print("AGENDAS_SERVICE buscar_agenda_por_uuid")
        print('url', url)
        try:
            response = requests.get(
                url,
                headers=self._default_headers,
                timeout=self.timeout_seconds
            )
            response.raise_for_status()
            logger.info(
                'Agenda buscada com sucesso (uuid=%s)',
                agenda_uuid,
            )
            return response
        except RequestException as exc:
            logger.error(
                'Erro ao buscar agenda (uuid=%s): %s',
                agenda_uuid,
                exc
            )
            raise
