"""
Serviço para geração de Ata de Escolha.
Baseado no padrão da Lauda de Convocação, mas com informações da escola escolhida.
"""
import logging
from typing import Dict, List, Optional, Union
from requests import RequestException

from .candidatos_api_service import CandidatosService


class CargoObrigatorioError(Exception):
    """Exceção levantada quando o processo tem mais de um cargo e o cargo não foi informado."""
    def __init__(self, cargos: List[Dict], message: str = "Selecione um cargo para emitir a Ata de Escolha."):
        self.cargos = cargos
        self.message = message
        super().__init__(message)
from .processo_convocacao_api_service import ProcessoConvocacaoService
from .agendas_api_service import AgendasService
from .escolhas_api_service import EscolhasService

logger = logging.getLogger(__name__)


class AtaEscolhaService:
    """
    Serviço para geração de Ata de Escolha.
    Processa por cargo (cargo_codigo) de forma independente: busca habilitados filtrando por cargo,
    organiza sessões conforme agendas do cargo, busca escolhas e consolida o resultado por cargo.
    """

    def __init__(
        self,
        candidatos_base_url: str = 'https://example.com',
        processo_base_url: str = 'https://example.com',
        agendas_base_url: str = 'https://example.com',
        escolhas_base_url: str = 'https://example.com',
        timeout_seconds: int = 30
    ):
        """
        Inicializa o serviço de ata de escolha.

        Args:
            candidatos_base_url: URL base da API de candidatos
            processo_base_url: URL base da API de processos de convocação
            agendas_base_url: URL base da API de agendas
            escolhas_base_url: URL base da API de escolhas
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
        self.escolhas_service = EscolhasService(
            base_url=escolhas_base_url,
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
        PCD deve aparecer primeiro.

        Args:
            candidatos: Lista de candidatos retornados da API

        Returns:
            Dicionário com candidatos separados por tipo:
            {
                'pcd': [candidatos com categoria_efetiva='PCD'],
                'geral': [candidatos com categoria_efetiva='GERAL'],
                'nna': [candidatos com categoria_efetiva='NNA']
            }
        """
        separados = {
            'pcd': [],
            'geral': [],
            'nna': []
        }

        for candidato in candidatos:
            categoria_efetiva = candidato.get('categoria_efetiva')

            # Separa por categoria_efetiva
            if categoria_efetiva == 'PCD':
                separados['pcd'].append(candidato)
            elif categoria_efetiva == 'GERAL':
                separados['geral'].append(candidato)
            elif categoria_efetiva == 'NNA':
                separados['nna'].append(candidato)

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
        Busca candidatos faltantes nos outros processos do mesmo concurso, filtrando por cargo quando informado.

        Args:
            outros_processos_uuid: Lista de UUIDs dos outros processos
            lacunas_geral: Lista de classificações faltantes (Geral)
            lacunas_nna: Lista de classificações faltantes (NNA)
            lacunas_pcd: Lista de classificações faltantes (PCD)
            codigo_cargo: Código(s) do cargo para filtrar (opcional)
            ordering: Campo para ordenação

        Returns:
            Dicionário com candidatos faltantes por tipo. Cada lista é uma lista de dicts diretamente
            e os itens são anotados com 'status_especial' para diferenciar já classificados/convocados.
        """
        candidatos_faltantes = {
            'geral': [],
            'nna': [],
            'pcd': []
        }

        if not outros_processos_uuid:
            return candidatos_faltantes
        try:
            # Buscar candidatos PCD faltantes primeiro (devem aparecer primeiro)
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

        except RequestException as exc:
            logger.warning(
                'Erro ao buscar candidatos faltantes nos outros processos: %s',
                exc
            )
            # Não levanta exceção, apenas retorna o que conseguiu buscar

        return candidatos_faltantes

    def _buscar_escolhas_por_candidatos(self, candidato_uuids: List[str]) -> Dict[str, Dict]:
        """
        Busca escolhas por lista de candidato_uuids e retorna um mapa candidato_uuid -> escolha.

        Args:
            candidato_uuids: Lista de UUIDs dos candidatos

        Returns:
            Dicionário mapeando candidato_uuid -> escolha (ou vazio se não houver escolha)
        """
        escolhas_map = {}
        
        if not candidato_uuids:
            return escolhas_map

        try:
            escolhas_data = self.escolhas_service.buscar_escolhas_por_candidatos(
                candidato_uuids=candidato_uuids,
                situacao=None  # Buscar todas as escolhas
            )

            # Criar mapa de escolhas por candidato_uuid
            for escolha in escolhas_data:
                candidato_uuid = escolha.get('candidato_uuid')
                if candidato_uuid:
                    escolhas_map[str(candidato_uuid)] = escolha

            logger.info(
                'Encontradas %d escolhas para %d candidatos',
                len(escolhas_map),
                len(candidato_uuids)
            )

        except RequestException as exc:
            logger.warning(
                'Erro ao buscar escolhas: %s',
                exc
            )
            # Não levanta exceção, apenas retorna mapa vazio

        return escolhas_map

    def _extrair_dados_escola_escolhida(self, escolha: Dict) -> Dict:
        """
        Extrai dados da escola escolhida de uma escolha.

        Args:
            escolha: Dicionário com dados da escolha

        Returns:
            Dicionário com dados da escola escolhida:
            {
                'codigo_eol': str,
                'dre_codigo': str,
                'dre_nome': str,
                'tipo_unidade': str,
                'nome_escola': str,
                'tipo_vaga': str  # 'P' para precária, 'D' para definitiva
            }
        """
        vaga_escola = escolha.get('vaga_escola', {})
        escola = vaga_escola.get('escola', {}) if isinstance(vaga_escola, dict) else {}
        dre = escola.get('dre', {}) if isinstance(escola, dict) else {}

        codigo_eol = escola.get('codigo_eol', '') if isinstance(escola, dict) else ''
        # DRE = SIGLA (do model dres)
        dre_codigo = dre.get('sigla', '') or dre.get('SIGLA', '') if isinstance(dre, dict) else ''
        dre_nome = dre.get('nome', '') if isinstance(dre, dict) else ''
        # TIPO UNIDADE = TIPO_UE (do model escola)
        tipo_unidade = escola.get('tipo_ue', '') or escola.get('TIPO_UE', '') or escola.get('tipo_unidade', '') if isinstance(escola, dict) else ''
        nome_escola = escola.get('nome_oficial', '') if isinstance(escola, dict) else ''

        # Converter tipo_vaga: 'precaria' = 'P', 'definitiva' = 'D'
        tipo_vaga_raw = escolha.get('tipo_vaga', '')
        if tipo_vaga_raw == 'precaria':
            tipo_vaga = 'P'
        elif tipo_vaga_raw == 'definitiva':
            tipo_vaga = 'D'
        else:
            tipo_vaga = ''

        return {
            'codigo_eol': codigo_eol,
            'dre_codigo': dre_codigo,
            'dre_nome': dre_nome,
            'tipo_unidade': tipo_unidade,
            'nome_escola': nome_escola,
            'tipo_vaga': tipo_vaga
        }

    def _contar_escolhas_por_situacao(self, escolhas: List[Dict]) -> Dict[str, int]:
        """
        Conta quantas escolhas existem por situação.
        A situação pode ser: 'escolha', 'nao-escolha' ou 'reconvocacao'.
        Retorna um dicionário com as chaves 'escolha', 'nao_escolha' e 'reconvocacao'.
        Também inclui alias 'nao-escolha' para compatibilidade de acesso.
        """
        contadores = {
            'escolha': 0,
            'nao_escolha': 0,
            'reconvocacao': 0,
        }

        normalizar = {
            'escolha': 'escolha',
            'nao-escolha': 'nao_escolha',
            'nao_escolha': 'nao_escolha',
            'reconvocacao': 'reconvocacao',
        }
        for escolha in escolhas:
            situacao_raw = escolha.get('situacao')
            if not isinstance(situacao_raw, str):
                continue
            situacao = situacao_raw.strip().lower()
            chave = normalizar.get(situacao)
            if chave in contadores:
                contadores[chave] += 1

        # Alias com hífen para acesso alternativo se necessário
        contadores['nao-escolha'] = contadores['nao_escolha']
        return contadores

    def _contar_escolhas_por_situacao_por_tipo(
        self,
        candidatos_sep_cargo: Dict[str, List[Dict]],
        escolhas_map: Dict[str, Dict]
    ) -> Dict[str, Dict[str, int]]:
        """
        Conta as escolhas por situação separadas por tipo de candidato (pcd, geral, nna).
        - candidatos_sep_cargo: {'pcd': [...], 'geral': [...], 'nna': [...]}
        - escolhas_map: {candidato_uuid: { 'situacao': 'escolha'|'nao-escolha'|'reconvocacao', ...}}
        """
        resultado: Dict[str, Dict[str, int]] = {}
        normalizar = {
            'escolha': 'escolha',
            'nao-escolha': 'nao_escolha',
            'nao_escolha': 'nao_escolha',
            'reconvocacao': 'reconvocacao',
        }
        for tipo in ('pcd', 'geral', 'nna'):
            candidatos_tipo = candidatos_sep_cargo.get(tipo) or []
            uuids_tipo = {
                str(c.get('uuid'))
                for c in candidatos_tipo
                if c.get('uuid') is not None
            }
            cont = {'escolha': 0, 'nao_escolha': 0, 'reconvocacao': 0}
            for cand_uuid in uuids_tipo:
                esc = escolhas_map.get(cand_uuid)
                if not esc:
                    continue
                situacao_raw = esc.get('situacao')
                if not isinstance(situacao_raw, str):
                    continue
                situacao = situacao_raw.strip().lower()
                chave = normalizar.get(situacao)
                if chave:
                    cont[chave] += 1
            cont['nao-escolha'] = cont['nao_escolha']
            resultado[tipo] = cont
        return resultado
    

    def processar_ata_escolha(
        self,
        processo_uuid: str,
        cargo_codigo: Optional[str] = None,
        ordering: str = 'ranking_escolha'
    ) -> Dict:
        """
        Processa a ata de escolha para um processo.

        Passos (por cargo):
        1. Busca candidatos habilitados do processo filtrando por cargo
        2. Separa candidatos por tipo (PCD primeiro, depois GERAL, depois NNA)
        3. Identifica lacunas nas classificações de cada tipo no contexto do cargo
        4. Busca detalhes do processo para obter concurso_uuid e os outros processos do concurso
        5. Busca candidatos faltantes nos outros processos (do mesmo cargo) e mescla na base do cargo
           respeitando lacunas de classificação
        6. Busca escolhas dos candidatos
        7. Divide os candidatos do cargo em sessões com base nas agendas do cargo
        8. Gera campo 'ordem_escolha' por cargo e retorna a estrutura final agregada por cargos

        Args:
            processo_uuid: UUID do processo de convocação
            cargo_codigo: Código do cargo (obrigatório se o processo tiver mais de um cargo)
            ordering: Campo para ordenação (padrão: 'ranking_escolha')

        Returns:
            Dicionário com os dados processados:
            {
                'processo_uuid': str,
                'concurso_uuid': str,
                'todos_processos_uuid': List[str],
                'outros_processos_uuid': List[str],
                'total_cargos': int,
                'cargos': [
                    {
                        'cargo_nome': str,
                        'cargo_codigo': str,
                        'numero_sessoes': int,
                        'sessoes': [
                            {
                                'numero_sessao': int,
                                'hora_convocacao_inicio': str,
                                'hora_convocacao_fim': str,
                                'horario_formatado': str,
                                'total_candidatos': int,
                                'candidatos': List[Dict]  # Cada candidato com dados da escolha se houver
                            },
                            ...
                        ]
                    },
                    ...
                ]
            }

            Cada candidato na lista terá os seguintes campos adicionais:
            - 'escolha': Dict com dados da escola escolhida (se houver escolha)
            - 'assinatura': str ('Escolha' ou 'Não Escolha')
            - 'codigo_eol': str
            - 'dre_codigo': str
            - 'dre_nome': str
            - 'tipo_unidade': str
            - 'nome_escola_escolhida': str
            - 'tipo_vaga': str ('P' ou 'D')

        Raises:
            RequestException: Em caso de erro nas requisições
            CargoObrigatorioError: Quando o processo tem mais de um cargo e cargo_codigo não foi informado
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

            # (codigos_cargo/codigo_cargo_param usados em outros pontos - manter compatibilidade)
            codigos_cargo = []
            for agenda in agendas_temp:
                cod = agenda.get('cargo_codigo')
                if cod and cod not in codigos_cargo:
                    codigos_cargo.append(cod)
            codigo_cargo_param = codigos_cargo[0] if len(codigos_cargo) == 1 else (codigos_cargo if codigos_cargo else None)
            logger.info('Códigos de cargo extraídos das agendas: %s', codigo_cargo_param)

            # Inicializar resultado e metadados globais
            resultado = {
                'processo_uuid': processo_uuid,
                'concurso_uuid': None,
            }
            processo_uuid_principal = None
            outros_processos_uuid = []

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
                cod = agenda.get('cargo_codigo')
                if cod not in agendas_por_cargo:
                    agendas_por_cargo[cod] = {
                        'cargo_nome': cargo_nome,
                        'cargo_codigo': cod,
                        'agendas': []
                    }
                agendas_por_cargo[cod]['agendas'].append(agenda)
                if not agendas_por_cargo[cod]['cargo_codigo'] and cod:
                    agendas_por_cargo[cod]['cargo_codigo'] = cod

            logger.info('Agendas agrupadas por cargo: %s', {c: len(info['agendas']) for c, info in agendas_por_cargo.items()})

            # Ata de escolha é gerada para um único cargo: exigir seleção se houver mais de um
            cargos_lista = [{'cargo_codigo': c, 'cargo_nome': info['cargo_nome']} for c, info in agendas_por_cargo.items()]
            if len(agendas_por_cargo) > 1:
                if not cargo_codigo:
                    raise CargoObrigatorioError(cargos=cargos_lista)
                if cargo_codigo not in agendas_por_cargo:
                    raise ValueError(f"Cargo '{cargo_codigo}' não encontrado no processo.")
                agendas_por_cargo = {cargo_codigo: agendas_por_cargo[cargo_codigo]}
            elif len(agendas_por_cargo) == 1 and cargo_codigo is None:
                # processo com um único cargo: usar esse cargo
                unico = next(iter(agendas_por_cargo.keys()))
                agendas_por_cargo = {unico: agendas_por_cargo[unico]}

            # 2. Processar cada cargo e separar por sessões/agendas
            cargos_com_sessoes = []

            response_processo = self.processo_service.buscar_processo_convocacao(processo_uuid)
            processo_data = response_processo.json()
            classificacoes_pcd, classificacoes_nna, classificacoes_geral = [], [], []

            for cargo_info in agendas_por_cargo.values():
                cargo_nome = cargo_info['cargo_nome']
                cargo_codigo = cargo_info['cargo_codigo']
                agendas_cargo = cargo_info['agendas']
                numero_sessoes = len(agendas_cargo)
                logger.info('Processando cargo: %s (%d sessões/agendas)', cargo_nome, numero_sessoes)

                # Coletar todos os UUIDs de candidatos das agendas deste cargo
                todos_candidatos_uuids = []
                for _agenda in agendas_cargo:
                    for _uuid in _agenda.get('candidatos_uuids', []):
                        if _uuid not in todos_candidatos_uuids:
                            todos_candidatos_uuids.append(_uuid)

                logger.info('Buscando candidatos por UUIDs (cargo=%s, total=%d)', cargo_codigo, len(todos_candidatos_uuids))
                response_candidatos = self.candidatos_service.buscar_por_uuids(
                    uuids=todos_candidatos_uuids,
                    order_by=ordering
                )
                dados_cargo = response_candidatos.json()
                if isinstance(dados_cargo, dict) and 'results' in dados_cargo:
                    candidatos_cargo = dados_cargo['results']
                elif isinstance(dados_cargo, list):
                    candidatos_cargo = dados_cargo
                else:
                    logger.warning('Resposta inesperada ao buscar candidatos por UUIDs para cargo %s', cargo_codigo)
                    candidatos_cargo = []

                # Separar por tipo e identificar lacunas por cargo (PCD primeiro)
                candidatos_sep_cargo = self._separar_por_tipo(candidatos_cargo)
                lacunas_geral = []
                lacunas_nna = []
                lacunas_pcd = []
                
                # Processar PCD primeiro
                if candidatos_sep_cargo['pcd']:
                    classificacoes_pcd = self._extrair_classificacoes(candidatos_sep_cargo['pcd'], 'classificacao_pcd')
                    lacunas_pcd = self._identificar_lacunas(classificacoes_pcd)
                
                if candidatos_sep_cargo['geral']:
                    classificacoes_geral = self._extrair_classificacoes(candidatos_sep_cargo['geral'], 'classificacao')
                    lacunas_geral = self._identificar_lacunas(classificacoes_geral)
                if candidatos_sep_cargo['nna']:
                    classificacoes_nna = self._extrair_classificacoes(candidatos_sep_cargo['nna'], 'classificacao_nna')
                    lacunas_nna = self._identificar_lacunas(classificacoes_nna)

                # Buscar e inserir faltantes deste cargo (se houver lacunas)
                faltantes_todos = []
                if lacunas_geral or lacunas_nna or lacunas_pcd:
                    if resultado.get('concurso_uuid') is None:
                        logger.info('Buscando detalhes do processo para processo_uuid=%s', processo_uuid)
                        concurso_uuid = processo_data.get('concurso_uuid')
                        resultado['concurso_uuid'] = concurso_uuid
                        if concurso_uuid:
                            logger.info('Buscando todos os processos do concurso %s', concurso_uuid)
                            processo_uuid_principal, outros_processos_uuid = self.processo_service.separar_processos_por_principal(
                                processo_data=processo_data
                            )
                            resultado['todos_processos_uuid'] = [processo_uuid_principal] + outros_processos_uuid
                            resultado['outros_processos_uuid'] = outros_processos_uuid
                    if outros_processos_uuid:
                        candidatos_faltantes = self._buscar_candidatos_faltantes(
                            outros_processos_uuid=outros_processos_uuid,
                            lacunas_geral=lacunas_geral,
                            lacunas_nna=lacunas_nna,
                            lacunas_pcd=lacunas_pcd,
                            codigo_cargo=cargo_codigo,
                            ordering=ordering
                        )
                        # Inserir PCD primeiro
                        if candidatos_faltantes['pcd']:
                            candidatos_faltantes['pcd'].sort(key=lambda x: x.get('classificacao_pcd') or float('inf'))
                            faltantes_todos.extend(candidatos_faltantes['pcd'])
                        if candidatos_faltantes['geral']:
                            candidatos_faltantes['geral'].sort(key=lambda x: x.get('classificacao') or float('inf'))
                            faltantes_todos.extend(candidatos_faltantes['geral'])
                        if candidatos_faltantes['nna']:
                            candidatos_faltantes['nna'].sort(key=lambda x: x.get('classificacao_nna') or float('inf'))
                            faltantes_todos.extend(candidatos_faltantes['nna'])

                # Ordenar base: PCD primeiro, depois por ranking_escolha e inserir faltantes por classificacao
                def key_ranking_escolha(item):
                    val = item.get('ranking_escolha')
                    return val if val is not None else float('inf')
                
                def key_categoria_efetiva(item):
                    # PCD primeiro (0), depois GERAL (1), depois NNA (2)
                    categoria = item.get('categoria_efetiva', '')
                    if categoria == 'PCD':
                        return 0
                    elif categoria == 'GERAL':
                        return 1
                    elif categoria == 'NNA':
                        return 2
                    return 3
                
                def key_classificacao(item):
                    val = item.get('classificacao')
                    return val if val is not None else float('inf')
                
                # Ordenar candidatos: primeiro por categoria (PCD primeiro), depois por ranking
                candidatos_base_ordenados = sorted(
                    candidatos_cargo,
                    key=lambda x: (key_categoria_efetiva(x), key_ranking_escolha(x))
                )
                
                if faltantes_todos:
                    # Helpers para encontrar lacunas e índices de inserção
                    def indices_lacunas_classificacao(classificacoes_ordenadas):
                        """Retorna mapa {valor_faltante: indice_insercao} sem repetir índice para lacunas múltiplas."""
                        gaps = {}
                        cont = 0
                        if not classificacoes_ordenadas:
                            return gaps
                        for i in range(len(classificacoes_ordenadas) - 1):
                            a = classificacoes_ordenadas[i]
                            b = classificacoes_ordenadas[i + 1]
                            if a is None or b is None:
                                continue
                            if isinstance(a, int) and isinstance(b, int) and b - a > 1:
                                # números faltantes entre a e b
                                # cada número faltante avança o índice de inserção
                                for offset, missing in enumerate(range(a + 1, b), start=1):
                                    gaps[missing] = i + offset + cont
                                cont += 1
                        return gaps

                    # Construir lista de classificações ordenadas a partir da base
                    def _classificacao_para_gap(item):
                        return 9999999 if item.get('categoria_efetiva') != 'GERAL' else item.get('classificacao')
                    classifs_base = [_classificacao_para_gap(c) for c in candidatos_base_ordenados if _classificacao_para_gap(c) is not None]
                    mapa_lacunas = indices_lacunas_classificacao(classifs_base)

                    for faltante in faltantes_todos:
                        cls_f = faltante.get('classificacao')
                        if cls_f in mapa_lacunas:
                            pos = mapa_lacunas[cls_f]
                            candidatos_base_ordenados.insert(pos, faltante)
                        else:
                            # Caso não exista lacuna correspondente, insere por ordem de classificação
                            # na posição ordenada padrão (bisect-like)
                            pos = 0
                            while pos < len(candidatos_base_ordenados) and key_classificacao(candidatos_base_ordenados[pos]) <= cls_f:
                                pos += 1
                            candidatos_base_ordenados.insert(pos, faltante)

                # Buscar escolhas dos candidatos
                candidato_uuids = [c.get('uuid') for c in candidatos_base_ordenados if c.get('uuid')]
                escolhas_map = self._buscar_escolhas_por_candidatos(candidato_uuids)

                # Adicionar informações de escolha aos candidatos e extrair dados do candidato
                for candidato in candidatos_base_ordenados:
                    candidato_uuid = candidato.get('uuid')
                    escolha = escolhas_map.get(str(candidato_uuid)) if candidato_uuid else None

                    # Extrair dados do candidato (nome, RG, CPF, RF)
                    candidato_obj = candidato.get('candidato', {}) if isinstance(candidato.get('candidato'), dict) else {}
                    candidato['nome'] = candidato_obj.get('nome', '') if isinstance(candidato_obj, dict) else ''
                    candidato['rg'] = candidato_obj.get('rg', '') if isinstance(candidato_obj, dict) else ''
                    candidato['cpf'] = candidato_obj.get('cpf', '') if isinstance(candidato_obj, dict) else ''
                    # RF = registro_funcional (do model candidato)
                    candidato['rf'] = candidato_obj.get('registro_funcional', '') if isinstance(candidato_obj, dict) else ''

                    if escolha and escolha.get('situacao') == 'escolha':
                        # Candidato fez escolha
                        dados_escola = self._extrair_dados_escola_escolhida(escolha)
                        candidato['escolha'] = dados_escola
                        candidato['assinatura'] = 'Escolha'
                        candidato['codigo_eol'] = dados_escola.get('codigo_eol', '')
                        candidato['dre_codigo'] = dados_escola.get('dre_codigo', '')
                        candidato['dre_nome'] = dados_escola.get('dre_nome', '')
                        candidato['tipo_unidade'] = dados_escola.get('tipo_unidade', '')
                        candidato['nome_escola_escolhida'] = dados_escola.get('nome_escola', '')
                        candidato['tipo_vaga'] = dados_escola.get('tipo_vaga', '')
                    else:
                        # Candidato não fez escolha
                        candidato['escolha'] = None
                        candidato['assinatura'] = 'Não Escolha'
                        candidato['codigo_eol'] = ''
                        candidato['dre_codigo'] = ''
                        candidato['dre_nome'] = ''
                        candidato['tipo_unidade'] = ''
                        candidato['nome_escola_escolhida'] = ''
                        candidato['tipo_vaga'] = ''

                # Processar agendas do cargo para encontrar separadores
                uuids_separadores_cargo = []
                acumulado = 0

                # Iterar nas agendas do cargo até o penúltimo item
                for i in range(len(agendas_cargo) - 1):  # Até o penúltimo
                    agenda = agendas_cargo[i]
                    candidatos_uuids = agenda.get('candidatos_uuids', [])
                    quantidade_candidatos = len(candidatos_uuids)

                    # Calcular posição: acumulado + quantidade
                    posicao = acumulado + quantidade_candidatos

                    # Verificar se a posição existe em candidatos_cargo
                    if posicao < len(candidatos_cargo):
                        candidato_separador = candidatos_cargo[posicao]
                        uuid_separador = candidatos_cargo[posicao].get('uuid')
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
                        'candidatos': candidatos_base_ordenados
                    })
                else:
                    # Iterar na lista de UUIDs separadores do cargo
                    for idx_uuid, uuid_separador in enumerate(uuids_separadores_cargo):
                        # Encontrar a posição do candidato com esse UUID em candidatos_base_ordenados
                        posicao_encontrada = None
                        for idx_candidato, candidato in enumerate(candidatos_base_ordenados):
                            if candidato.get('uuid') == uuid_separador and idx_candidato not in indices_usados:
                                posicao_encontrada = idx_candidato
                                break

                        if posicao_encontrada is not None:
                            # Determinar o índice inicial
                            if idx_uuid == 0:
                                indice_inicial = 0
                            else:
                                indice_inicial = max(indices_usados) + 1 if indices_usados else 0

                            # Criar lista desde indice_inicial até posicao_encontrada (apenas deste cargo)
                            lista_segmento = candidatos_base_ordenados[indice_inicial:posicao_encontrada]
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
                                if indice_proximo < len(candidatos_base_ordenados):
                                    lista_final = candidatos_base_ordenados[indice_proximo:]
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

            # A estrutura principal será organizada por cargos e sessões
            resultado_estruturado = {
                'processo_uuid': processo_data.get('uuid'),
                'processo_nome': processo_data.get('descricao'),
                'concurso_uuid': resultado.get('concurso_uuid'),
                'todos_processos_uuid': resultado.get('todos_processos_uuid'),
                'outros_processos_uuid': resultado.get('outros_processos_uuid'),
                'total_cargos': len(cargos_com_sessoes),
                'candidatos_sep_cargo': candidatos_sep_cargo,
                # Totais agregados por situação (todas as escolhas)
                'escolhas_totais': self._contar_escolhas_por_situacao(list(escolhas_map.values())),
                # Totais por situação separados por tipo (pcd/geral/nna)
                'escolhas_totais_por_tipo': self._contar_escolhas_por_situacao_por_tipo(
                    candidatos_sep_cargo=candidatos_sep_cargo,
                    escolhas_map=escolhas_map
                ),
                'cargos': [],
                'intervalos_classificacoes': {
                    'pcd': {
                        'min': min(classificacoes_pcd) if classificacoes_pcd else 0,
                        'max': max(classificacoes_pcd) if classificacoes_pcd else 0
                    },
                    'geral': {
                        'min': min(classificacoes_geral) if classificacoes_geral else 0 ,
                        'max': max(classificacoes_geral) if classificacoes_geral else 0
                    },
                    'nna': {
                        'min': min(classificacoes_nna) if classificacoes_nna else 0,
                        'max': max(classificacoes_nna) if classificacoes_nna else 0
                    }
                }
            }

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
            # Retornar a estrutura organizada
            return resultado_estruturado

        except RequestException as exc:
            logger.error(
                'Erro ao processar ata de escolha (processo_uuid=%s): %s',
                processo_uuid,
                exc
            )
            raise
        except Exception as exc:
            logger.error(
                'Erro inesperado ao processar ata de escolha (processo_uuid=%s): %s',
                processo_uuid,
                exc
            )
            raise
