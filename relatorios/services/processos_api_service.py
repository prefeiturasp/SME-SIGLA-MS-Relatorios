"""
Serviços para integração com API de processos de convocação.
"""
import logging
from typing import Optional, Dict, Any
import requests
from requests import RequestException

logger = logging.getLogger(__name__)


class ProcessosService:
    def __init__(self, base_url: str = 'https://example.com', timeout_seconds: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self._default_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def buscar_cargos_por_processo(
        self,
        processo_uuid: str
    ) -> requests.Response:
        """
        Busca cargos do processo de convocação por processo_uuid.
        
        Args:
            processo_uuid: UUID do processo de convocação
            
        Returns:
            Response da API com os cargos do processo
            
        Raises:
            RequestException: Em caso de erro na requisição
        """
        url = f"{self.base_url}/api/v1/processos-convocacao/{processo_uuid}/cargos/"
        
        try:
            response = requests.get(
                url,
                headers=self._default_headers,
                timeout=self.timeout_seconds
            )
            response.raise_for_status()
            logger.info('Cargos do processo buscados com sucesso (processo_uuid=%s)', processo_uuid)
            return response
        except RequestException as exc:
            logger.error('Erro ao buscar cargos do processo: %s', exc)
            raise

