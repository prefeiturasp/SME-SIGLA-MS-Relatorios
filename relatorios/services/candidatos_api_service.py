"""
Serviços para integração com API de candidatos.
"""
import logging
from typing import Optional, Dict, Any
import requests
from requests import RequestException

logger = logging.getLogger(__name__)


class CandidatosService:
    def __init__(self, base_url: str = 'https://example.com', timeout_seconds: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self._default_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def buscar_concurso_candidatos_por_processo(
        self,
        processo_uuid: str
    ) -> requests.Response:
        """
        Busca ConcursoCandidato por processo_uuid.
        Tenta usar o endpoint /api/v1/candidatos/ que pode retornar ConcursoCandidato
        através do relacionamento 'concursos'.
        
        Args:
            processo_uuid: UUID do processo de convocação
            
        Returns:
            Response da API com os dados (pode ser Candidato ou ConcursoCandidato)
            
        Raises:
            RequestException: Em caso de erro na requisição
        """
        # O endpoint /api/v1/candidatos/ pode retornar Candidato com relacionamento concursos
        # Ou pode ter uma lógica customizada que retorna ConcursoCandidato
        # Vamos tentar buscar e ver o que retorna
        url = f"{self.base_url}/api/v1/habilitados/"
        
        params = {
            'processo_uuid': processo_uuid,
            'page_size': 10000,
        }
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self._default_headers,
                timeout=self.timeout_seconds
            )
            response.raise_for_status()
            logger.info('Dados buscados via /api/v1/habilitados/ (processo_uuid=%s)', processo_uuid)
            return response
        except RequestException as exc:
            logger.error('Erro ao buscar ConcursoCandidato: %s', exc)
            raise

