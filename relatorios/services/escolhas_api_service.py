"""
Serviços para integração com API de escolhas.
"""
import logging
from typing import Optional, Dict, Any
import requests
from requests import RequestException

logger = logging.getLogger(__name__)

class EscolhasService:
    def __init__(self, base_url: str = 'https://example.com', timeout_seconds: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self._default_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def buscar_vagas_escolas(
        self,
        processo_uuid: str   
    ) -> requests.Response:
        """
        Busca vagas de escolas por processo_uuid.
        
        Args:
            processo_uuid: UUID do processo de convocação
            headers: Headers HTTP opcionais para a requisição
            
        Returns:
            Response da API com as vagas das escolas
            
        Raises:
            RequestException: Em caso de erro na requisição
        """
        url = f"{self.base_url}/api/v1/vagas-escolas/"
 
        
        params = {
            'processo_uuid': processo_uuid,
        }
        
        try:
            response = requests.get(
                url,
                params=params,
                headers= self._default_headers,
                timeout=self.timeout_seconds
            )
            response.raise_for_status()
            logger.info('Vagas de escolas buscadas com sucesso (processo_uuid=%s)', processo_uuid)
            return response
        except RequestException as exc:
            logger.error('Erro ao buscar vagas de escolas: %s', exc)
            raise
