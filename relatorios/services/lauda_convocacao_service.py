"""
Serviço para geração de lauda de convocação.
"""
import logging
from typing import Dict, List, Optional, Set, Union
from requests import RequestException

from .candidatos_api_service import CandidatosService
from .processo_convocacao_api_service import ProcessoConvocacaoService
from .agendas_api_service import AgendasService

logger = logging.getLogger(__name__)


class LaudaConvocacaoService:
    """
    Service para geração de lauda de convocação.
    """
    
    def __init__(
        self,
        candidatos_base_url: str = 'https://example.com',
        processo_base_url: str = 'https://example.com',
        agendas_base_url: str = 'https://example.com',
        timeout_seconds: int = 30
    ):
        """
        Inicializa o serviço de lauda de convocação.
        
        Args:
            candidatos_base_url: URL base da API de candidatos
            processo_base_url: URL base da API de processos de convocação
            agendas_base_url: URL base da API de agendas
            timeout_seconds: Timeout em segundos para as requisições
        """
        self.candidatos_service = CandidatosService(
            base_url=candidatos_base_url,
            timeout_seconds=timeout_seconds
        )
        self.processo_service = ProcessoConvocacaoService(
            base_url=processo_base_url,
            timeout_seconds=timeout_seconds
        )
        self.agendas_service = AgendasService(
            base_url=agendas_base_url,
            timeout_seconds=timeout_seconds
        )
    
    def _identificar_lacunas(self, classificacoes: List[int]) -> List[int]:
        """
        Identifica lacunas em uma lista de classificações.
        
        Exemplo: [1, 2, 3, 6, 7] -> retorna [4, 5]
        
        Args:
            classificacoes: Lista de classificações (pode conter None)
            
        Returns:
            Lista de classificações faltantes (lacunas)
        """
        # Remove None e valores inválidos, ordena e remove duplicatas
        classificacoes_validas = sorted(set(c for c in classificacoes if c is not None and isinstance(c, int)))
        
        if not classificacoes_validas:
            return []
        
        # Encontra o mínimo e máximo
        min_class = min(classificacoes_validas)
        max_class = max(classificacoes_validas)
        
        # Cria um conjunto com todas as classificações esperadas
        todas_classificacoes = set(range(min_class, max_class + 1))
        
        # Identifica as lacunas (classificações esperadas que não existem)
        lacunas = sorted(todas_classificacoes - set(classificacoes_validas))
        
        return lacunas
    
    def _separar_por_tipo(self, candidatos: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Separa candidatos por tipo usando o campo categoria_efetiva: GERAL, NNA e PCD.
        
        Args:
            candidatos: Lista de candidatos retornados da API
            
        Returns:
            Dicionário com candidatos separados por tipo:
            {
                'geral': [candidatos com categoria_efetiva='GERAL'],
                'nna': [candidatos com categoria_efetiva='NNA'],
                'pcd': [candidatos com categoria_efetiva='PCD']
            }
        """
        separados = {
            'geral': [],
            'nna': [],
            'pcd': []
        }
        
        for candidato in candidatos:
            categoria_efetiva = candidato.get('categoria_efetiva')
            
            # Separa por categoria_efetiva
            if categoria_efetiva == 'GERAL':
                separados['geral'].append(candidato)
            elif categoria_efetiva == 'NNA':
                separados['nna'].append(candidato)
            elif categoria_efetiva == 'PCD':
                separados['pcd'].append(candidato)
        
        return separados
    
    def _extrair_classificacoes(self, candidatos: List[Dict], campo: str) -> List[int]:
        """
        Extrai classificações de uma lista de candidatos.
        
        Args:
            candidatos: Lista de candidatos
            campo: Nome do campo de classificação ('classificacao', 'classificacao_nna', 'classificacao_pcd')
            
        Returns:
            Lista de classificações (pode conter None)
        """
        return [candidato.get(campo) for candidato in candidatos]
    
    def _buscar_candidatos_faltantes(
        self,
        outros_processos_uuid: List[str],
        lacunas_geral: List[int],
        lacunas_nna: List[int],
        lacunas_pcd: List[int],
        codigo_cargo: Optional[Union[List[str], str]] = None,
        ordering: str = 'ranking_escolha'
    ) -> Dict[str, List[Dict]]:
        """
        Busca candidatos faltantes nos outros processos do mesmo concurso.
        
        Args:
            outros_processos_uuid: Lista de UUIDs dos outros processos
            lacunas_geral: Lista de classificações faltantes (Geral)
            lacunas_nna: Lista de classificações faltantes (NNA)
            lacunas_pcd: Lista de classificações faltantes (PCD)
            codigo_cargo: Código(s) do cargo para filtrar (opcional)
            ordering: Campo para ordenação
            
        Returns:
            Dicionário com candidatos faltantes por tipo
        """
        candidatos_faltantes = {
            'geral': [],
            'nna': [],
            'pcd': []
        }
        
        if not outros_processos_uuid:
            return candidatos_faltantes
        try:
            # Buscar candidatos Gerais faltantes
            if lacunas_geral:
                logger.info(
                    'Buscando candidatos Gerais faltantes (classificações: %s) nos processos: %s',
                    lacunas_geral,
                    outros_processos_uuid
                )
                response_geral = self.candidatos_service.buscar_habilitados_por_processos_e_classificacoes(
                    processo_uuids=outros_processos_uuid,
                    classificacao=lacunas_geral,
                    codigo_cargo=codigo_cargo,
                    ordering=ordering
                )
                candidatos_geral_data = response_geral.json()
                
                # candidatos_geral_data é uma lista de dicts diretamente
                if isinstance(candidatos_geral_data, list):
                    candidatos_faltantes['geral'] = candidatos_geral_data
                else:
                    candidatos_faltantes['geral'] = [] 
                
                for candidato in candidatos_faltantes['geral']:
                    candidato['status_especial'] = 'JÁ CONVOCADO - LEI 13.398/02' if candidato.get('classificacao_nna') is not None else 'JÁ CONVOCADO - LEI 15.939/13' if candidato.get('classificacao_pcd') is not None else ''
                
                logger.info(
                    'Encontrados %d candidatos Gerais faltantes',
                    len(candidatos_faltantes['geral'])   
                )       
            
            # Buscar candidatos NNA faltantes
            if lacunas_nna:
                logger.info(
                    'Buscando candidatos NNA faltantes (classificações: %s) nos processos: %s',
                    lacunas_nna,
                    outros_processos_uuid
                )
                response_nna = self.candidatos_service.buscar_habilitados_por_processos_e_classificacoes(
                    processo_uuids=outros_processos_uuid,
                    classificacao_nna=lacunas_nna,
                    codigo_cargo=codigo_cargo,
                    ordering=ordering
                )
                candidatos_nna_data = response_nna.json()
                
                # candidatos_nna_data é uma lista de dicts diretamente
                if isinstance(candidatos_nna_data, list):
                    candidatos_faltantes['nna'] = candidatos_nna_data
                else:
                    candidatos_faltantes['nna'] = []
                
                # Marcar candidatos como "CANDIDATOS JÁ CLASSIFICADO."
                for candidato in candidatos_faltantes['nna']:
                    candidato['status_especial'] = 'CANDIDATOS JÁ CLASSIFICADO.'
                
                logger.info(
                    'Encontrados %d candidatos NNA faltantes',
                    len(candidatos_faltantes['nna'])
                )
            
            # Buscar candidatos PCD faltantes
            # Nota: O método atual não suporta classificacao_pcd diretamente,
            # então vamos buscar todos os candidatos dos outros processos e filtrar
            if lacunas_pcd:
                logger.info(
                    'Buscando candidatos PCD faltantes (classificações: %s) nos processos: %s',
                    lacunas_pcd,
                    outros_processos_uuid
                )
                
                # Buscar todos os candidatos dos outros processos (sem filtro de classificação)
                todos_candidatos_pcd = []
                for processo_uuid in outros_processos_uuid:
                    try:
                        response_pcd = self.candidatos_service.buscar_habilitados(
                            processo_uuid=processo_uuid,
                            ordering=ordering
                        )
                        candidatos_pcd_data = response_pcd.json()
                        
                        # candidatos_pcd_data é uma lista de dicts diretamente
                        if isinstance(candidatos_pcd_data, list):
                            todos_candidatos_pcd.extend(candidatos_pcd_data)
                    except RequestException as exc:
                        logger.warning(
                            'Erro ao buscar candidatos do processo %s: %s',
                            processo_uuid,
                            exc
                        )
                
                # Filtrar apenas candidatos PCD com classificações nas lacunas
                candidatos_faltantes['pcd'] = [
                    c for c in todos_candidatos_pcd
                    if c.get('classificacao_pcd') is not None and c.get('classificacao_pcd') in lacunas_pcd
                ]
                
                # Marcar candidatos como "CANDIDATOS JÁ CLASSIFICADO."
                for candidato in candidatos_faltantes['pcd']:
                    candidato['status_especial'] = 'CANDIDATOS JÁ CLASSIFICADO.'
                
                logger.info(
                    'Encontrados %d candidatos PCD faltantes',
                    len(candidatos_faltantes['pcd'])
                )
            
        except RequestException as exc:
            logger.warning(
                'Erro ao buscar candidatos faltantes nos outros processos: %s',
                exc
            )
            # Não levanta exceção, apenas retorna o que conseguiu buscar
        
        return candidatos_faltantes
    
    def processar_lauda_convocacao(
        self,
        processo_uuid: str,
        ordering: str = 'ranking_escolha'
    ) -> Dict:
        """
        Processa a lauda de convocação para um processo.
        
        Passos:
        1. Busca candidatos habilitados usando buscar_habilitados
        2. Separa candidatos por tipo (Geral, NNA, PCD)
        3. Identifica lacunas nas classificações de cada tipo
        4. Busca detalhes do processo para obter concurso_uuid
        5. Busca todos os processos do mesmo concurso usando separar_processos_por_principal
        6. Busca candidatos faltantes nos outros processos e os adiciona à lista
           (candidatos faltantes são marcados com status_especial='CANDIDATOS JÁ CLASSIFICADO.')
        
        Args:
            processo_uuid: UUID do processo de convocação
            ordering: Campo para ordenação (padrão: 'ranking_escolha')
            
        Returns:
            Dicionário com os dados processados:
            {
                'processo_uuid': str,
                'concurso_uuid': str,
                'todos_processos_uuid': List[str],
                'outros_processos_uuid': List[str],
                'candidatos': {
                    'geral': {
                        'candidatos': List[Dict],  # Inclui candidatos faltantes marcados
                        'classificacoes': List[int],
                        'lacunas': List[int]
                    },
                    'nna': {
                        'candidatos': List[Dict],  # Inclui candidatos faltantes marcados
                        'classificacoes': List[int],
                        'lacunas': List[int]
                    },
                    'pcd': {
                        'candidatos': List[Dict],  # Inclui candidatos faltantes marcados
                        'classificacoes': List[int],
                        'lacunas': List[int]
                    }
                }
            }
            
            Nota: Candidatos faltantes (encontrados em outros processos) terão o campo
            'status_especial' = 'CANDIDATOS JÁ CLASSIFICADO.'
            
        Raises:
            RequestException: Em caso de erro nas requisições
        """
        try:

            # 1. Buscar agendas do processo
            logger.info('Buscando agendas para processo_uuid=%s', processo_uuid)
            response_agendas = self.agendas_service.buscar_agendas(
                processo_convocacao_uuid=processo_uuid,
                page=1,
                page_size=1000000)

            # Extrair códigos de cargo das agendas
            agendas_data_temp = response_agendas.json()
            if isinstance(agendas_data_temp, dict) and 'results' in agendas_data_temp:
                agendas_temp = agendas_data_temp['results']
            elif isinstance(agendas_data_temp, list):
                agendas_temp = agendas_data_temp
            else:
                agendas_temp = []
            
            # Extrair códigos únicos de cargo
            codigos_cargo = []
            for agenda in agendas_temp:
                cargo_codigo = agenda.get('cargo_codigo')
                if cargo_codigo and cargo_codigo not in codigos_cargo:
                    codigos_cargo.append(cargo_codigo)

            # Converter para string única se houver apenas um, ou lista se houver múltiplos
            codigo_cargo_param = codigos_cargo[0] if len(codigos_cargo) == 1 else (codigos_cargo if codigos_cargo else None)
            
            logger.info('Códigos de cargo extraídos das agendas: %s', codigo_cargo_param)

            # 1. Buscar candidatos habilitados
            logger.info('Buscando candidatos habilitados para processo_uuid=%s', processo_uuid)
            response_candidatos = self.candidatos_service.buscar_habilitados(
                processo_uuid=processo_uuid,
                ordering=ordering
            )
            candidatos_data = response_candidatos.json()
            
            logger.info('Total de candidatos encontrados: %d', len(candidatos_data))
            
            # 4. Separar candidatos por tipo
            candidatos_separados = self._separar_por_tipo(candidatos_data)
            
            logger.info(
                'Candidatos separados - Geral: %d, NNA: %d, PCD: %d',
                len(candidatos_separados['geral']),
                len(candidatos_separados['nna']),
                len(candidatos_separados['pcd'])
            )   

            # Inicializar variáveis de lacunas
            lacunas_geral = []
            lacunas_nna = []
            lacunas_pcd = []
            
            # Inicializar resultado
            resultado = {
                'processo_uuid': processo_uuid,
                'concurso_uuid': None,
                'candidatos': {}
            }

            # Processar candidatos Gerais
            if candidatos_separados['geral']:
                classificacoes_geral = self._extrair_classificacoes(
                    candidatos_separados['geral'],
                    'classificacao'
                )
                lacunas_geral = self._identificar_lacunas(classificacoes_geral)
                
                resultado['candidatos']['geral'] = {
                    'candidatos': candidatos_separados['geral'],
                    'classificacoes': sorted(set(c for c in classificacoes_geral if c is not None)),
                    'lacunas': lacunas_geral
                }
            
            # Processar candidatos NNA
            if candidatos_separados['nna']:
                classificacoes_nna = self._extrair_classificacoes(
                    candidatos_separados['nna'],
                    'classificacao_nna'
                )
                lacunas_nna = self._identificar_lacunas(classificacoes_nna)
                
                resultado['candidatos']['nna'] = {
                    'candidatos': candidatos_separados['nna'],
                    'classificacoes': sorted(set(c for c in classificacoes_nna if c is not None)),
                    'lacunas': lacunas_nna
                }
            
            # Processar candidatos PCD
            if candidatos_separados['pcd']:
                classificacoes_pcd = self._extrair_classificacoes(
                    candidatos_separados['pcd'],
                    'classificacao_pcd'
                )
                lacunas_pcd = self._identificar_lacunas(classificacoes_pcd)
                
                resultado['candidatos']['pcd'] = {
                    'candidatos': candidatos_separados['pcd'],
                    'classificacoes': sorted(set(c for c in classificacoes_pcd if c is not None)),
                    'lacunas': lacunas_pcd
                } 
            
            if lacunas_geral or lacunas_nna or lacunas_pcd:
                # 5. Buscar detalhes do processo para obter concurso_uuid
                logger.info('Buscando detalhes do processo para processo_uuid=%s', processo_uuid)
                response_processo = self.processo_service.buscar_processo_convocacao(processo_uuid)
                processo_data = response_processo.json()
                
                concurso_uuid = processo_data.get('concurso_uuid')
                resultado['concurso_uuid'] = concurso_uuid

                if concurso_uuid:
                    # 6. Buscar todos os processos do mesmo concurso usando separar_processos_por_principal
                    logger.info('Buscando todos os processos do concurso %s', concurso_uuid)
                    processo_uuid_principal, outros_processos_uuid = self.processo_service.separar_processos_por_principal(
                        processo_uuid_principal=processo_uuid
                    )
                    
                    resultado['todos_processos_uuid'] = [processo_uuid_principal] + outros_processos_uuid
                    resultado['outros_processos_uuid'] = outros_processos_uuid
                    
                    # 7. Buscar candidatos faltantes nos outros processos
                    if outros_processos_uuid:
                        candidatos_faltantes = self._buscar_candidatos_faltantes(
                            outros_processos_uuid=outros_processos_uuid,
                            lacunas_geral=lacunas_geral,
                            lacunas_nna=lacunas_nna,
                            lacunas_pcd=lacunas_pcd,
                            codigo_cargo=codigo_cargo_param,
                            ordering=ordering
                        )
                        
                        # Adicionar candidatos faltantes às listas existentes, removendo duplicatas
                        if candidatos_faltantes['geral']:
                            if 'geral' not in resultado['candidatos']:
                                resultado['candidatos']['geral'] = {
                                    'candidatos': [],
                                    'classificacoes': [],
                                    'lacunas': lacunas_geral
                                }
                            
                            # Ordenar candidatos faltantes por classificação crescente
                            candidatos_faltantes['geral'].sort(key=lambda x: x.get('classificacao') or float('inf'))
                            resultado['candidatos']['geral']['candidatos'].extend(candidatos_faltantes['geral'])
                            # Ordenar lista final por classificação crescente
                            resultado['candidatos']['geral']['candidatos'].sort(key=lambda x: x.get('classificacao') or float('inf'))
                            
                            logger.info(
                                'Adicionados %d candidatos Gerais faltantes à lista',
                                len(candidatos_faltantes['geral'])
                            )
                        
                        if candidatos_faltantes['nna']:
                            if 'nna' not in resultado['candidatos']:
                                resultado['candidatos']['nna'] = {
                                    'candidatos': [],
                                    'classificacoes': [],
                                    'lacunas': lacunas_nna
                                }
                            
                            # Ordenar candidatos faltantes por classificação crescente
                            candidatos_faltantes['nna'].sort(key=lambda x: x.get('classificacao_nna') or float('inf'))
                            resultado['candidatos']['nna']['candidatos'].extend(candidatos_faltantes['nna'])
                            # Ordenar lista final por classificação crescente
                            resultado['candidatos']['nna']['candidatos'].sort(key=lambda x: x.get('classificacao_nna') or float('inf'))
                            
                            logger.info(
                                'Adicionados %d candidatos NNA faltantes à lista',
                                len(candidatos_faltantes['nna'])
                            )
                        
                        if candidatos_faltantes['pcd']:
                            if 'pcd' not in resultado['candidatos']:
                                resultado['candidatos']['pcd'] = {
                                    'candidatos': [],
                                    'classificacoes': [],
                                    'lacunas': lacunas_pcd
                                }
                            
                            # Ordenar candidatos faltantes por classificação crescente
                            candidatos_faltantes['pcd'].sort(key=lambda x: x.get('classificacao_pcd') or float('inf'))
                            resultado['candidatos']['pcd']['candidatos'].extend(candidatos_faltantes['pcd'])
                            # Ordenar lista final por classificação crescente
                            resultado['candidatos']['pcd']['candidatos'].sort(key=lambda x: x.get('classificacao_pcd') or float('inf'))
                            
                            logger.info(
                                'Adicionados %d candidatos PCD faltantes à lista',
                                len(candidatos_faltantes['pcd'])
                            )
            
            # Coletar todos os candidatos de todos os tipos
            todos_candidatos = []
            if 'pcd' in resultado['candidatos']:
                todos_candidatos.extend(resultado['candidatos']['pcd'].get('candidatos', []))
            if 'geral' in resultado['candidatos']:
                todos_candidatos.extend(resultado['candidatos']['geral'].get('candidatos', []))
            if 'nna' in resultado['candidatos']:
                todos_candidatos.extend(resultado['candidatos']['nna'].get('candidatos', []))
            
            # Processar agendas para separar candidatos
            agendas_data = response_agendas.json()
            
            # Extrair lista de agendas
            if isinstance(agendas_data, dict) and 'results' in agendas_data:
                agendas = agendas_data['results']
            elif isinstance(agendas_data, list):
                agendas = agendas_data
            else:
                agendas = []
            
            # 1. Agrupar agendas por cargo_nome e salvar cargo_codigo
            agendas_por_cargo = {}
            for agenda in agendas:
                cargo_nome = agenda.get('cargo_nome', 'Sem Cargo')
                cargo_codigo = agenda.get('cargo_codigo')
                if cargo_nome not in agendas_por_cargo:
                    agendas_por_cargo[cargo_nome] = {
                        'cargo_nome': cargo_nome,
                        'cargo_codigo': cargo_codigo,
                        'agendas': []
                    }
                agendas_por_cargo[cargo_nome]['agendas'].append(agenda)
                # Garantir que cargo_codigo seja atualizado se não estava definido
                if not agendas_por_cargo[cargo_nome]['cargo_codigo'] and cargo_codigo:
                    agendas_por_cargo[cargo_nome]['cargo_codigo'] = cargo_codigo
            
            logger.info('Agendas agrupadas por cargo: %s', {cargo: len(info['agendas']) for cargo, info in agendas_por_cargo.items()})
            
            # 2. Processar cada cargo e separar por sessões/agendas
            cargos_com_sessoes = []
            
            for cargo_info in agendas_por_cargo.values():
                cargo_nome = cargo_info['cargo_nome']
                cargo_codigo = cargo_info['cargo_codigo']
                agendas_cargo = cargo_info['agendas']
                numero_sessoes = len(agendas_cargo)
                logger.info('Processando cargo: %s (%d sessões/agendas)', cargo_nome, numero_sessoes)
                
                # Filtrar candidatos por cargo (se disponível)
                candidatos_cargo = [
                    c for c in todos_candidatos
                    if c.get('cargo_codigo') == cargo_codigo or not c.get('cargo_codigo')
                ]

                print('='*100)
                print(candidatos_cargo)
                print(todos_candidatos[0]['descricao_cargo'])
                print(cargo_nome)
                print('#'*100)
                
                # Se não encontrou candidatos filtrados, usar todos
                if not candidatos_cargo:
                    candidatos_cargo = todos_candidatos
                
                # Processar agendas do cargo para encontrar separadores
                uuids_separadores_cargo = []
                acumulado = 0
                
                # Filtrar candidatos_data por cargo para calcular posições corretas
                candidatos_data_cargo = [
                    c for c in candidatos_data
                    if c.get('cargo_codigo') == cargo_codigo or not c.get('cargo_codigo')
                ]
                
                if not candidatos_data_cargo:
                    candidatos_data_cargo = candidatos_data
                
                # Iterar nas agendas do cargo até o penúltimo item
                for i in range(len(agendas_cargo) - 1):  # Até o penúltimo
                    agenda = agendas_cargo[i]
                    candidatos_uuids = agenda.get('candidatos_uuids', [])
                    quantidade_candidatos = len(candidatos_uuids)
                    
                    # Calcular posição: acumulado + quantidade
                    posicao = acumulado + quantidade_candidatos
                    
                    # Verificar se a posição existe em candidatos_data_cargo
                    if posicao < len(candidatos_data_cargo):
                        candidato_separador = candidatos_data_cargo[posicao]
                        uuid_separador = candidato_separador.get('uuid')
                        if uuid_separador:
                            uuids_separadores_cargo.append(uuid_separador)
                            logger.info(
                                'Cargo %s - Agenda %d: quantidade=%d, posição=%d, UUID separador=%s',
                                cargo_nome,
                                i + 1,
                                quantidade_candidatos,
                                posicao,
                                uuid_separador
                            )
                    
                    # Atualizar acumulado para próxima iteração
                    acumulado += quantidade_candidatos
                
                # 3. Separar candidatos do cargo baseado nos UUIDs separadores
                # Mapear cada sessão com sua agenda correspondente para obter horários
                sessoes_cargo = []
                indices_usados = set()
                
                if not uuids_separadores_cargo:
                    # Se não há separadores, todos os candidatos vão para uma única sessão
                    # Usar a primeira agenda para obter horários
                    agenda_primeira = agendas_cargo[0] if agendas_cargo else {}
                    sessoes_cargo.append({
                        'numero_sessao': 1,
                        'hora_convocacao_inicio': agenda_primeira.get('hora_convocacao_inicio', ''),
                        'hora_convocacao_fim': agenda_primeira.get('hora_convocacao_fim', ''),
                        'candidatos': candidatos_cargo
                    })
                else:
                    # Iterar na lista de UUIDs separadores do cargo
                    for idx_uuid, uuid_separador in enumerate(uuids_separadores_cargo):
                        # Encontrar a posição do candidato com esse UUID em candidatos_cargo
                        posicao_encontrada = None
                        for idx_candidato, candidato in enumerate(candidatos_cargo):
                            if candidato.get('uuid') == uuid_separador and idx_candidato not in indices_usados:
                                posicao_encontrada = idx_candidato
                                break
                        
                        if posicao_encontrada is not None:
                            # Determinar o índice inicial
                            if idx_uuid == 0:
                                indice_inicial = 0
                            else:
                                indice_inicial = max(indices_usados) + 1 if indices_usados else 0
                            
                            # Criar lista desde indice_inicial até posicao_encontrada
                            lista_segmento = candidatos_cargo[indice_inicial:posicao_encontrada]
                            if lista_segmento:
                                # Obter horários da agenda correspondente (índice da sessão)
                                numero_sessao = len(sessoes_cargo) + 1
                                agenda_sessao = agendas_cargo[numero_sessao - 1] if numero_sessao - 1 < len(agendas_cargo) else {}
                                
                                sessoes_cargo.append({
                                    'numero_sessao': numero_sessao,
                                    'hora_convocacao_inicio': agenda_sessao.get('hora_convocacao_inicio', ''),
                                    'hora_convocacao_fim': agenda_sessao.get('hora_convocacao_fim', ''),
                                    'candidatos': lista_segmento
                                })
                            
                            # Marcar índices como utilizados
                            for i in range(indice_inicial, posicao_encontrada):
                                indices_usados.add(i)
                            
                            logger.info(
                                'Cargo %s - Sessão %d: %d candidatos (índice %d até %d) - Horário: %s às %s',
                                cargo_nome,
                                len(sessoes_cargo),
                                len(lista_segmento),
                                indice_inicial,
                                posicao_encontrada,
                                agenda_sessao.get('hora_convocacao_inicio', 'N/A'),
                                agenda_sessao.get('hora_convocacao_fim', 'N/A')
                            )
                            
                            # Se for o último UUID, criar sessão adicional da posição em diante
                            if idx_uuid == len(uuids_separadores_cargo) - 1:
                                indice_proximo = posicao_encontrada
                                if indice_proximo < len(candidatos_cargo):
                                    lista_final = candidatos_cargo[indice_proximo:]
                                    if lista_final:
                                        # Obter horários da última agenda
                                        numero_sessao_final = len(sessoes_cargo) + 1
                                        agenda_final = agendas_cargo[numero_sessao_final - 1] if numero_sessao_final - 1 < len(agendas_cargo) else {}
                                        
                                        sessoes_cargo.append({
                                            'numero_sessao': numero_sessao_final,
                                            'hora_convocacao_inicio': agenda_final.get('hora_convocacao_inicio', ''),
                                            'hora_convocacao_fim': agenda_final.get('hora_convocacao_fim', ''),
                                            'candidatos': lista_final
                                        })
                                        logger.info(
                                            'Cargo %s - Sessão %d (final): %d candidatos - Horário: %s às %s',
                                            cargo_nome,
                                            len(sessoes_cargo),
                                            len(lista_final),
                                            agenda_final.get('hora_convocacao_inicio', 'N/A'),
                                            agenda_final.get('hora_convocacao_fim', 'N/A')
                                        )
                
                # Adicionar estrutura do cargo com suas sessões
                cargos_com_sessoes.append({
                    'cargo_nome': cargo_nome,
                    'cargo_codigo': cargo_codigo,
                    'numero_sessoes': numero_sessoes,
                    'sessoes': sessoes_cargo
                })
            
            # 4. Printar a estrutura de cargos com sessões
            print('*' * 100)
            print(f"Total de candidatos: {len(todos_candidatos)}")
            print(f"Total de cargos: {len(cargos_com_sessoes)}")
            
            for cargo_info in cargos_com_sessoes:
                cargo_nome = cargo_info['cargo_nome']
                numero_sessoes = cargo_info['numero_sessoes']
                sessoes = cargo_info['sessoes']
                
                print(f"\n{'='*100}")
                print(f"CARGO: {cargo_nome}")
                print(f"Número de Sessões: {numero_sessoes}")
                print(f"{'='*100}")
                
                for sessao in sessoes:
                    numero_sessao = sessao['numero_sessao']
                    hora_inicio = sessao.get('hora_convocacao_inicio', '')
                    hora_fim = sessao.get('hora_convocacao_fim', '')
                    candidatos_sessao = sessao['candidatos']
                    
                    # Formatar horário
                    if hora_inicio and hora_fim:
                        horario_formatado = f"Horário: {hora_inicio} às {hora_fim}"
                    else:
                        horario_formatado = "Horário: Não informado"
                    
                    print(f"\n{numero_sessao}ª SESSÃO - {horario_formatado} ({len(candidatos_sessao)} candidatos):")
                    for candidato in candidatos_sessao:
                        print(f" Cargo - {candidato.get('codigo_cargo')}  - {candidato.get('uuid')} - {candidato.get('candidato', {}).get('nome', 'N/A')} - GERAL: {candidato.get('classificacao')} - NNA: {candidato.get('classificacao_nna')} - PCD: {candidato.get('classificacao_pcd')} - Categoria: {candidato.get('categoria_efetiva')} - Status: {candidato.get('status_especial')}")
            
            print('*' * 100)
            
            # Adicionar campo "ordem_escolha" aos candidatos
            # A ordem é contínua entre sessões do mesmo cargo, mas reinicia para cada novo cargo
            # Candidatos com status_especial não são contados na ordem
            for cargo_info in cargos_com_sessoes:
                ordem_escolha_contador = 0  # Reinicia para cada cargo
                
                for sessao in cargo_info['sessoes']:
                    candidatos_sessao = sessao.get('candidatos', [])
                    
                    for candidato in candidatos_sessao:
                        # Se o candidato não tiver status_especial, adicionar ordem_escolha
                        if not candidato.get('status_especial'):
                            ordem_escolha_contador += 1
                            candidato['ordem_escolha'] = ordem_escolha_contador
                        else:
                            # Candidatos com status_especial não recebem ordem_escolha
                            candidato['ordem_escolha'] = None
            
            # Reestruturar resultado conforme a estrutura dos prints
            # A estrutura principal será organizada por cargos e sessões
            resultado_estruturado = {
                'processo_uuid': resultado.get('processo_uuid'),
                'concurso_uuid': resultado.get('concurso_uuid'),
                'todos_processos_uuid': resultado.get('todos_processos_uuid'),
                'outros_processos_uuid': resultado.get('outros_processos_uuid'),
                'total_candidatos': len(todos_candidatos),
                'total_cargos': len(cargos_com_sessoes),
                'cargos': []
            }
            
            # Estruturar cada cargo com suas sessões (conforme estrutura dos prints)
            for cargo_info in cargos_com_sessoes:
                cargo_estruturado = {
                    'cargo_nome': cargo_info['cargo_nome'],
                    'cargo_codigo': cargo_info.get('cargo_codigo'),
                    'numero_sessoes': cargo_info['numero_sessoes'],
                    'sessoes': []
                }
                
                for sessao in cargo_info['sessoes']:
                    hora_inicio = sessao.get('hora_convocacao_inicio', '')
                    hora_fim = sessao.get('hora_convocacao_fim', '')
                    candidatos_sessao = sessao.get('candidatos', [])
                    
                    # Formatar horário
                    if hora_inicio and hora_fim:
                        horario_formatado = f"{hora_inicio} às {hora_fim}"
                    else:
                        horario_formatado = "Não informado"
                    
                    sessao_estruturada = {
                        'numero_sessao': sessao['numero_sessao'],
                        'hora_convocacao_inicio': hora_inicio,
                        'hora_convocacao_fim': hora_fim,
                        'horario_formatado': horario_formatado,
                        'total_candidatos': len(candidatos_sessao),
                        'candidatos': candidatos_sessao
                    }
                    cargo_estruturado['sessoes'].append(sessao_estruturada)
                
                resultado_estruturado['cargos'].append(cargo_estruturado)
            
            # Retornar a estrutura organizada conforme os prints
            return resultado_estruturado
            
        except RequestException as exc:
            logger.error(
                'Erro ao processar lauda de convocação (processo_uuid=%s): %s',
                processo_uuid,
                exc
            )
            raise
        except Exception as exc:
            logger.error(
                'Erro inesperado ao processar lauda de convocação (processo_uuid=%s): %s',
                processo_uuid,
                exc
            )
            raise
    
    # def Gerar(self, processo_uuid: str, ordering: str = 'ranking_escolha'):
    #     """
    #     Método que chama processar_lauda_convocacao e imprime o resultado.
        
    #     Args:
    #         processo_uuid: UUID do processo de convocação
    #         ordering: Campo para ordenação (padrão: 'ranking_escolha')
    #     """
    #     resultado = self.processar_lauda_convocacao(processo_uuid, ordering)
    #     print(resultado)
    #     return resultado
