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

    def buscar_escolhas_por_candidatos(
        self,
        candidato_uuids: list,
        situacao: str = 'nao-escolha'
    ) -> list:
        """
        Busca escolhas por lista de candidato_uuids filtrando por situação.
        
        Args:
            candidato_uuids: Lista de UUIDs dos candidatos
            situacao: Situação da escolha (padrão: 'nao-escolha'). Se None, retorna todas as escolhas.
            
        Returns:
            Lista de escolhas filtradas por situação (ou todas se situacao=None)
            
        Raises:
            RequestException: Em caso de erro na requisição
        """
        url = f"{self.base_url}/api/v1/escolhas/busca/"
        
        data = {
            'candidato_uuid': candidato_uuids,
        }
        
        try:
            response = requests.post(
                url,
                json=data,
                headers=self._default_headers,
                timeout=self.timeout_seconds
            )
            response.raise_for_status()
            
            # A resposta pode ser uma lista ou um dict com 'results'
            escolhas_data = response.json()
            if isinstance(escolhas_data, list):
                escolhas = escolhas_data
            elif isinstance(escolhas_data, dict) and 'results' in escolhas_data:
                escolhas = escolhas_data.get('results', [])
            else:
                escolhas = []
            
            # Filtrar por situação apenas se situacao não for None
            if situacao is None:
                escolhas_filtradas = escolhas
            else:
                escolhas_filtradas = [e for e in escolhas if e.get('situacao') == situacao]
            
            logger.info('Escolhas buscadas com sucesso (candidatos=%d, situacao=%s, filtradas=%d)', 
                       len(candidato_uuids), situacao, len(escolhas_filtradas))
            return escolhas_filtradas
        
        except RequestException as exc:
            logger.error('Erro ao buscar escolhas: %s', exc)
            raise
