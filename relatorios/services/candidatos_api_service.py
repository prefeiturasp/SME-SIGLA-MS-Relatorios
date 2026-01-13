"""
Serviços para integração com API de candidatos.
"""
import logging
from typing import Optional, List, Union, Dict, Any
import requests
from requests import RequestException

logger = logging.getLogger(__name__)


class CandidatosService:
    """
    Service para integração com API de candidatos.
    """
    
    def __init__(self, base_url: str = 'https://example.com', timeout_seconds: int = 30):
        """
        Inicializa o serviço de candidatos.
        
        Args:
            base_url: URL base da API de candidatos
            timeout_seconds: Timeout em segundos para as requisições
        """
        self.base_url = base_url.rstrip('/')
        self.timeout_seconds = timeout_seconds
        self._default_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }

    def buscar_habilitados(
        self,
        processo_uuid: str,
        codigo_cargo: Optional[Union[List[str], str]] = None,
        ordering: str = 'ranking_escolha'
    ) -> requests.Response:
        """
        Busca candidatos habilitados por processo_uuid, ordenados por ranking_escolha.
        
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
            'processo_uuid': processo_uuid,
            'ordering': ordering,
        }
        if codigo_cargo is not None:
            if isinstance(codigo_cargo, list):
                if len(codigo_cargo) > 1:
                    params['codigo_cargo__in'] = ','.join(str(c) for c in codigo_cargo)
                elif len(codigo_cargo) == 1:
                    params['codigo_cargo'] = str(codigo_cargo[0])
            else:
                codigo_cargo_param = str(codigo_cargo)
                if ',' in codigo_cargo_param:
                    params['codigo_cargo__in'] = codigo_cargo_param
                else:
                    params['codigo_cargo'] = codigo_cargo_param
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self._default_headers,
                timeout=self.timeout_seconds
            )
            response.raise_for_status()
            logger.info(
                'Candidatos habilitados buscados com sucesso (processo_uuid=%s, codigo_cargo=%s, ordering=%s)',
                processo_uuid,
                params.get('codigo_cargo') or params.get('codigo_cargo__in'),
                ordering
            )
            return response
        except RequestException as exc:
            logger.error(
                'Erro ao buscar candidatos habilitados (processo_uuid=%s, codigo_cargo=%s): %s',
                processo_uuid,
                params.get('codigo_cargo') or params.get('codigo_cargo__in'),
                exc
            )
            raise

    def buscar_habilitados_por_processos_e_classificacoes(
        self,
        processo_uuids: Union[List[str], str],
        classificacao: Optional[Union[List[int], List[str], str]] = None,
        classificacao_nna: Optional[Union[List[int], List[str], str]] = None,
        codigo_cargo: Optional[Union[List[str], str]] = None,
        ordering: str = 'ranking_escolha'
    ) -> requests.Response:
        """
        Busca candidatos habilitados em múltiplos processos com classificações específicas.
        Suporta filtros por classificacao e/ou classificacao_nna de forma flexível.
        
        Args:
            processo_uuids: Lista de UUIDs dos processos ou string com UUIDs separados por vírgula
            classificacao: Lista de classificações ou string com classificações separadas por vírgula (opcional)
            classificacao_nna: Lista de classificações NNA ou string com classificações separadas por vírgula (opcional)
            codigo_cargo: Lista de códigos de cargo ou string com códigos separados por vírgula (opcional)
            ordering: Campo para ordenação (padrão: 'ranking_escolha')
            
        Returns:
            Response da API com os candidatos habilitados
            
        Raises:
            RequestException: Em caso de erro na requisição
        """
        url = f"{self.base_url}/api/v1/habilitados/"
        
        # Normaliza processo_uuids para string separada por vírgula
        if isinstance(processo_uuids, list):
            processo_uuid_param = ','.join(processo_uuids)
        else:
            processo_uuid_param = processo_uuids
        
        params = {
            'ordering': ordering,
        }
        
        # Adiciona processo_uuid - django-filter aceita vírgulas com sufixo __in
        # Para múltiplos valores, usa o formato: processo_uuid__in=uuid1,uuid2
        if isinstance(processo_uuids, list):
            if len(processo_uuids) > 1:
                params['processo_uuid__in'] = ','.join(processo_uuids)
            else:
                params['processo_uuid'] = processo_uuids[0]
        else:
            # String: verifica se tem vírgula (múltiplos valores)
            if ',' in processo_uuid_param:
                params['processo_uuid__in'] = processo_uuid_param
            else:
                params['processo_uuid'] = processo_uuid_param
        
        # Adiciona classificacao se fornecido
        # django-filter aceita vírgulas: classificacao__in=1,2,3
        if classificacao is not None:
            if isinstance(classificacao, list):
                classificacao_param = ','.join(str(c) for c in classificacao)
                if len(classificacao) > 1:
                    params['classificacao__in'] = classificacao_param
                else:
                    params['classificacao'] = classificacao_param
            else:
                classificacao_param = str(classificacao)
                if ',' in classificacao_param:
                    params['classificacao__in'] = classificacao_param
                else:
                    params['classificacao'] = classificacao_param
        
        # Adiciona classificacao_nna se fornecido
        # django-filter aceita vírgulas: classificacao_nna__in=1,2,3
        if classificacao_nna is not None:
            if isinstance(classificacao_nna, list):
                classificacao_nna_param = ','.join(str(c) for c in classificacao_nna)
                if len(classificacao_nna) > 1:
                    params['classificacao_nna__in'] = classificacao_nna_param
                else:
                    params['classificacao_nna'] = classificacao_nna_param
            else:
                classificacao_nna_param = str(classificacao_nna)
                if ',' in classificacao_nna_param:
                    params['classificacao_nna__in'] = classificacao_nna_param
                else:
                    params['classificacao_nna'] = classificacao_nna_param
        
        # Adiciona codigo_cargo se fornecido
        # django-filter aceita vírgulas: codigo_cargo__in=cod1,cod2
        if codigo_cargo is not None:
            if isinstance(codigo_cargo, list):
                codigo_cargo_param = ','.join(str(c) for c in codigo_cargo)
                if len(codigo_cargo) > 1:
                    params['codigo_cargo__in'] = codigo_cargo_param
                else:
                    params['codigo_cargo'] = codigo_cargo_param
            else:
                codigo_cargo_param = str(codigo_cargo)
                if ',' in codigo_cargo_param:
                    params['codigo_cargo__in'] = codigo_cargo_param
                else:
                    params['codigo_cargo'] = codigo_cargo_param
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self._default_headers,
                timeout=self.timeout_seconds
            )
            response.raise_for_status()
            logger.info(
                'Candidatos habilitados buscados com sucesso (processo_uuids=%s, classificacao=%s, classificacao_nna=%s, codigo_cargo=%s, ordering=%s)',
                processo_uuid_param,
                params.get('classificacao'),
                params.get('classificacao_nna'),
                params.get('codigo_cargo'),
                ordering
            )
            return response
        except RequestException as exc:
            logger.error(
                'Erro ao buscar candidatos habilitados (processo_uuids=%s, classificacao=%s, classificacao_nna=%s, codigo_cargo=%s): %s',
                processo_uuid_param,
                params.get('classificacao'),
                params.get('classificacao_nna'),
                params.get('codigo_cargo'),
                exc
            )
            raise

    def buscar_por_uuids(
        self,
        uuids: List[str],
        order_by: str = 'ranking_escolha'
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
            'order_by': order_by,
        }
        
        payload = {
            'uuids': uuids
        }
        
        try:
            response = requests.post(
                url,
                params=params,
                json=payload,
                headers=self._default_headers,
                timeout=self.timeout_seconds
            )
            response.raise_for_status()
            logger.info(
                'Candidatos buscados por UUIDs com sucesso (total_uuids=%d, order_by=%s)',
                len(uuids),
                order_by
            )
            return response
        except RequestException as exc:
            logger.error(
                'Erro ao buscar candidatos por UUIDs (total_uuids=%d, order_by=%s): %s',
                len(uuids),
                order_by,
                exc
            )
            raise

    def buscar_candidatos_por_agendas(
        self,
        agendas_response: requests.Response,
        order_by: str = 'ranking_escolha'
    ) -> Dict:
        """
        Itera sobre as agendas retornadas e busca candidatos para cada agenda
        usando os candidatos_uuids de cada uma.
        
        Args:
            agendas_response: Response da API de agendas (deve conter 'results' com lista de agendas)
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
            
            # Extrair lista de agendas (pode estar em 'results' ou ser uma lista direta)
            if isinstance(agendas_data, dict) and 'results' in agendas_data:
                agendas = agendas_data['results']
            elif isinstance(agendas_data, list):
                agendas = agendas_data
            else:
                agendas = []
            
            logger.info('Processando %d agendas para buscar candidatos', len(agendas))
            
            resultado = {
                'agendas': []
            }
            
            for agenda in agendas:
                candidatos_uuids = agenda.get('candidatos_uuids', [])
                
                if not candidatos_uuids:
                    logger.warning(
                        'Agenda %s não possui candidatos_uuids',
                        agenda.get('uuid', 'desconhecido')
                    )
                    resultado['agendas'].append({
                        'agenda': agenda,
                        'candidatos': []
                    })
                    continue
                
                try:
                    # Buscar candidatos usando os UUIDs da agenda
                    response_candidatos = self.buscar_por_uuids(
                        uuids=candidatos_uuids,
                        order_by=order_by
                    )
                    
                    candidatos_data = response_candidatos.json()
                    
                    # Extrair lista de candidatos (pode ser uma lista direta ou um objeto com 'results')
                    if isinstance(candidatos_data, dict) and 'results' in candidatos_data:
                        candidatos = candidatos_data['results']
                    elif isinstance(candidatos_data, list):
                        candidatos = candidatos_data
                    else:
                        candidatos = []
                    
                    logger.info(
                        'Encontrados %d candidatos para agenda %s (de %d UUIDs)',
                        len(candidatos),
                        agenda.get('uuid', 'desconhecido'),
                        len(candidatos_uuids)
                    )
                    
                    resultado['agendas'].append({
                        'agenda': agenda,
                        'candidatos': candidatos
                    })
                    
                except RequestException as exc:
                    logger.error(
                        'Erro ao buscar candidatos para agenda %s: %s',
                        agenda.get('uuid', 'desconhecido'),
                        exc
                    )
                    # Adiciona a agenda mesmo com erro, mas sem candidatos
                    resultado['agendas'].append({
                        'agenda': agenda,
                        'candidatos': [],
                        'erro': str(exc)
                    })
            
            logger.info(
                'Processamento concluído: %d agendas processadas',
                len(resultado['agendas'])
            )
            
            return resultado
            
        except Exception as exc:
            logger.error(
                'Erro ao processar agendas e buscar candidatos: %s',
                exc
            )
            raise

