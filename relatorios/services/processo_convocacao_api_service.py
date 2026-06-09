"""Serviços para integração com API de processos de convocação."""
from __future__ import annotations
from typing import Any
import logging
import requests
from requests import RequestException
from sigla_sdk.context import get_correlation_id
from sigla_sdk.http.api_client import http_client
logger = logging.getLogger(__name__)

class ProcessoConvocacaoService:
    """Service para integração com API de processos de convocação."""

    def __init__(self, base_url: str='https://example.com', timeout_seconds: int=30) -> None:
        """Inicializa o serviço de processos de convocação.
        
        Args:
            self: Instância do objeto.
            base_url: URL base da API de processos de convocação.
            timeout_seconds: Timeout em segundos para as requisições.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self._default_headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def buscar_processo_convocacao(self, processo_uuid: str) -> requests.Response:
        """Busca um processo de convocação por UUID.
        
        Args:
            self: Instância do objeto.
            processo_uuid: UUID do processo de convocação.
        
        Returns:
            Resposta HTTP com o resultado da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        url = f'{self.base_url}/api/v1/processos-convocacao/{processo_uuid}/'
        logger.info('Buscando processo de convocação', extra={'correlation_id': get_correlation_id(), 'method': 'GET', 'url': url, 'headers': self._default_headers, 'processo_uuid': processo_uuid})
        try:
            response = http_client.get(url, headers=self._default_headers, timeout=self.timeout_seconds)
            response.raise_for_status()
        except RequestException as exc:
            logger.error('Erro ao buscar processo de convocação (processo_uuid=%s): %s', processo_uuid, exc)
            raise
        logger.info('Processo de convocação encontrado', extra={'correlation_id': get_correlation_id(), 'method': 'GET', 'url': url, 'headers': self._default_headers, 'processo_uuid': processo_uuid, 'status_code': response.status_code, 'response': str(response.json())[:100]})
        return response  # type: ignore[no-any-return]

    def buscar_processos_por_concurso(self, concurso_uuid: str) -> requests.Response:
        """Busca processos de convocação por concurso_uuid.
        
        Args:
            self: Instância do objeto.
            concurso_uuid: UUID do concurso.
        
        Returns:
            Resposta HTTP com o resultado da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        url = f'{self.base_url}/api/v1/processos-convocacao/'
        params = {'concurso_uuid': concurso_uuid}
        logger.info('Buscando processos de convocação por concurso', extra={'correlation_id': get_correlation_id(), 'method': 'GET', 'url': url, 'headers': self._default_headers, 'params': params})
        try:
            response = http_client.get(url, params=params, headers=self._default_headers, timeout=self.timeout_seconds)
            response.raise_for_status()
        except RequestException as exc:
            logger.error('Erro ao buscar processos de convocação (concurso_uuid=%s): %s', concurso_uuid, exc)
            raise
        logger.info('Processos de convocação por concursos encontrados', extra={'correlation_id': get_correlation_id(), 'method': 'GET', 'url': url, 'headers': self._default_headers, 'params': params, 'status_code': response.status_code, 'response': str(response.json())[:100]})
        return response  # type: ignore[no-any-return]

    def separar_processos_por_principal(self, processo_data: dict) -> tuple[str, list[str]]:
        """Busca o processo principal e outros processos do mesmo concurso,.
        
        Args:
            self: Instância do objeto.
            processo_data: Dicionário com os dados do processo principal.
        
        Returns:
            Resultado da operação.
        
        Raises:
            ValueError: Se o processo principal não for encontrado ou não tiver.
        """
        logger.info('Separando processos por principal', extra={'correlation_id': get_correlation_id(), 'processo_data': processo_data})
        concurso_uuid = processo_data.get('concurso_uuid')
        if not concurso_uuid:
            raise ValueError(f'Processo {processo_data.get('uuid')} não possui concurso_uuid')
        response_processos = self.buscar_processos_por_concurso(concurso_uuid)
        processos_data = response_processos.json()
        if isinstance(processos_data, dict) and 'results' in processos_data:
            processos_list = processos_data['results']
        elif isinstance(processos_data, list):
            processos_list = processos_data
        else:
            processos_list = [processos_data]
        outros_processos_uuid = []
        for processo in processos_list:
            processo_uuid = processo.get('uuid') or processo.get('id')
            if processo_uuid and processo_uuid != processo_data.get('uuid'):
                outros_processos_uuid.append(processo_uuid)
        logger.info('Processos por principal separados', extra={'correlation_id': get_correlation_id(), 'processo_data': processo_data, 'processos_list': processos_list, 'outros_processos_uuid': outros_processos_uuid})
        return (processo_data.get('uuid'), outros_processos_uuid)  # type: ignore[return-value]
