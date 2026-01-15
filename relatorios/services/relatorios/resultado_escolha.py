import logging
import re
from datetime import datetime
from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from django.http import HttpResponse
from io import BytesIO
from relatorios.services.base.relatorio_base import RelatorioBase
from relatorios.services.escolhas_api_service import EscolhasService
from relatorios.services.candidatos_api_service import CandidatosService
from relatorios.services.processos_api_service import ProcessosService
from relatorios.services.agendas_api_service import AgendasService

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

logger = logging.getLogger(__name__)


class ResultadoEscolha(RelatorioBase):
    """
    Classe concreta responsável por gerar o relatório de Resultado da Escolha SIM.
    Estrutura: Cargo > Agenda > Candidatos e escolha
    """
    
    TEMPLATE_NAME = 'relatorios/resultado_escolha_sim.html'
    
    def __init__(self, tipo: str):
        """Inicializa o service com as dependências necessárias."""
        self.escolhas_service = EscolhasService(base_url=settings.ESCOLHAS_API_URL)
        self.candidatos_service = CandidatosService(base_url=settings.CANDIDATOS_API_URL)
        self.processos_service = ProcessosService(base_url=settings.PROCESSOS_API_URL)
        self.agendas_service = AgendasService(base_url=settings.AGENDAS_API_URL)
        self.tipo = tipo
    
    def gerar(self, processo_uuid: str, request, formato: str = 'html', cabecalho: str = ''):
        """
        Gera o relatório de Resultado da Escolha SIM.
        
        Args:
            processo_uuid: UUID do processo de convocação
            request: Objeto request do Django
            formato: Formato do relatório ('html', 'pdf', 'xls' ou 'docx')
            cabecalho: Texto do cabeçalho do relatório (opcional)
        
        Returns:
            Tupla (HttpResponse, dados) onde:
            - HttpResponse: resposta com o relatório gerado (HTML, PDF, XLS ou DOCX)
            - dados: estrutura de dados do relatório (cargos_list) para salvar no banco
        """
        # Buscar cargos do processo para mapear código -> nome (fallback caso descricao_cargo não venha)
        print(f"Tipo de relatório: {self.tipo}")

        cargos_map = {}
        try:
            cargos_response = self.processos_service.buscar_cargos_por_processo(
                processo_uuid=str(processo_uuid) if processo_uuid else '',
            )
            cargos_data = cargos_response.json()
            cargos = cargos_data if isinstance(cargos_data, list) else []

            for cargo in cargos:
                codigo = cargo.get('cargo_codigo') or cargo.get('codigo_cargo') or ''
                nome = cargo.get('cargo_nome') or cargo.get('nome') or ''
                if codigo and nome:
                    cargos_map[str(codigo)] = nome
                    if isinstance(codigo, (int, float)):
                        cargos_map[codigo] = nome
        except Exception as exc:
            logger.warning('Falha ao buscar cargos do processo: %s. Continuando sem mapeamento de cargos.', exc)
        
        # Buscar agendas por processo_uuid
        agendas_map = {}  # Mapa agenda_uuid -> agenda_data
        agendas_por_candidato = {}  # Mapa candidato_uuid -> agenda_data (para relacionar escolhas com agendas)
        try:
            agendas_response = self.agendas_service.buscar_agendas(
                processo_convocacao_uuid=str(processo_uuid) if processo_uuid else '',
                page=1,
                page_size=1000  # Buscar todas as agendas
            )
            agendas_data = agendas_response.json()
            agendas = agendas_data.get('results', []) if isinstance(agendas_data, dict) else agendas_data
            
            for agenda in agendas:
                agenda_uuid = agenda.get('uuid')
                if agenda_uuid:
                    agendas_map[str(agenda_uuid)] = agenda
                    # Criar mapa inverso: candidato_uuid -> agenda
                    candidatos_uuids = agenda.get('candidatos_uuids', [])
                    for candidato_uuid in candidatos_uuids:
                        if candidato_uuid:
                            candidato_uuid_str = str(candidato_uuid)
                            # Se já existe uma agenda para este candidato, manter a primeira encontrada
                            # (ou podemos usar a última, dependendo da lógica de negócio)
                            if candidato_uuid_str not in agendas_por_candidato:
                                agendas_por_candidato[candidato_uuid_str] = agenda
        except Exception as exc:
            logger.warning('Falha ao buscar agendas do processo: %s. Continuando sem agendas.', exc)
        
        # Buscar ConcursoCandidato por processo_uuid
        try:
            candidatos_response = self.candidatos_service.buscar_concurso_candidatos_por_processo(
                processo_uuid=str(processo_uuid) if processo_uuid else '',
            )
            candidatos_data = candidatos_response.json()
            candidatos = candidatos_data.get('results', []) if isinstance(candidatos_data, dict) else candidatos_data
        except Exception as exc:
            logger.error('Falha ao buscar candidatos da API externa: %s', exc)
            raise
        
        # Criar mapa de candidatos por uuid para busca rápida
        candidatos_map = {}
        for candidato in candidatos:
            candidato_uuid = candidato.get('uuid')
            if candidato_uuid:
                candidatos_map[str(candidato_uuid)] = candidato
        
        # Extrair UUIDs dos ConcursoCandidato para buscar escolhas
        concurso_candidato_uuids = [candidato.get('uuid') for candidato in candidatos if candidato.get('uuid')]
        
        # Buscar escolhas com situação 'escolha' usando os UUIDs dos ConcursoCandidato
        tipo_escolha = 'escolha' if self.tipo == 'RESULTADO_ESCOLHA_SIM' else 'nao-escolha' if self.tipo == 'RESULTADO_ESCOLHA_NAO' else 'reconvocacao' if self.tipo == 'RESULTADO_ESCOLHA_RECONVOCACAO' else None
        try:
            escolhas_data = self.escolhas_service.buscar_escolhas_por_candidatos(
                candidato_uuids=concurso_candidato_uuids,
                situacao=tipo_escolha
            )
        except Exception as exc:
            logger.error('Falha ao buscar escolhas da API externa: %s', exc)
            raise

        # Processar escolhas e vincular com candidatos e agendas
        escolhas_com_candidatos = []
        for escolha in escolhas_data:
            candidato_uuid = escolha.get('candidato_uuid')
            if not candidato_uuid:
                continue

            candidato = candidatos_map.get(str(candidato_uuid)) or candidatos_map.get(candidato_uuid)
            if not candidato:
                continue
            
            # Extrair dados do candidato
            candidato_obj = candidato.get('candidato', {}) if isinstance(candidato.get('candidato'), dict) else {}
            
            # Obter classificações (do ConcursoCandidato)
            classificacao_geral = candidato.get('classificacao') or '-'
            classificacao_def = candidato.get('classificacao_pcd') or '-'
            classificacao_nna = candidato.get('classificacao_nna') or '-'
            
            # Obter nome, RG e CPF (do Candidato)
            nome = candidato_obj.get('nome') or '-'
            rg = candidato_obj.get('rg') or '-'
            cpf = candidato_obj.get('cpf') or '-'
            
            # Buscar agenda relacionada ao candidato através do mapa inverso
            agenda_data = agendas_por_candidato.get(str(candidato_uuid))
            
            # Se não encontrou agenda pelo candidato, tentar buscar pelo cargo do candidato
            if not agenda_data:
                cargo_codigo_candidato = candidato.get('codigo_cargo') or ''
                # Tentar buscar agenda pelo cargo_codigo
                for agenda in agendas_map.values():
                    if agenda.get('cargo_codigo') == cargo_codigo_candidato:
                        agenda_data = agenda
                        break
            
            # Se ainda não encontrou, criar uma agenda vazia para agrupamento
            if not agenda_data:
                cargo_codigo_candidato = candidato.get('codigo_cargo') or ''
                cargo_descricao_candidato = candidato.get('descricao_cargo') or ''
                if not cargo_descricao_candidato and cargo_codigo_candidato:
                    cargo_descricao_candidato = cargos_map.get(str(cargo_codigo_candidato)) or cargos_map.get(cargo_codigo_candidato) or ''
                if not cargo_descricao_candidato and cargo_codigo_candidato:
                    cargo_descricao_candidato = f"Cargo {cargo_codigo_candidato}"
                elif not cargo_descricao_candidato:
                    cargo_descricao_candidato = "Cargo não informado"
                
                agenda_data = {
                    'uuid': None,
                    'cargo_uuid': None,
                    'cargo_nome': cargo_descricao_candidato,
                    'cargo_codigo': cargo_codigo_candidato,
                    'escolha_em': None,
                    'sessao': None,
                }
            
            # Obter cargo da agenda (não do candidato)
            cargo_codigo = agenda_data.get('cargo_codigo') or ''
            cargo_descricao = agenda_data.get('cargo_nome') or ''
            
            # Se não encontrou descrição do cargo na agenda, buscar no mapa de cargos
            if not cargo_descricao and cargo_codigo:
                cargo_descricao = cargos_map.get(str(cargo_codigo)) or cargos_map.get(cargo_codigo) or ''
            
            # Se ainda não encontrou descrição mas tem código, usar o código como fallback
            if not cargo_descricao and cargo_codigo:
                cargo_descricao = f"Cargo {cargo_codigo}"
            elif not cargo_descricao:
                cargo_descricao = "Cargo não informado"
            
            # Valor da escolha baseado no tipo
            if self.tipo == 'RESULTADO_ESCOLHA_RECONVOCACAO':
                escolha_valor = 'R'
            elif self.tipo == 'RESULTADO_ESCOLHA_NAO':
                escolha_valor = 'N'
            elif self.tipo == 'RESULTADO_ESCOLHA_SIM':
                escolha_valor = 'S'
            else:
                escolha_valor = '-'
            
            escolhas_com_candidatos.append({
                'cargo_codigo': cargo_codigo,
                'cargo_descricao': cargo_descricao,
                'agenda_uuid': agenda_data.get('uuid'),
                'agenda_nome': agenda_data.get('cargo_nome') or cargo_descricao,
                'agenda_data': agenda_data.get('escolha_em') or '-',
                'agenda_sessao': agenda_data.get('sessao') or '-',
                'classificacao_geral': classificacao_geral,
                'classificacao_def': classificacao_def,
                'classificacao_nna': classificacao_nna,
                'nome': nome,
                'rg': rg,
                'cpf': cpf,
                'escolha': escolha_valor,
            })
        
        # Agrupar por cargo, depois por agenda
        cargos_list = self._agrupar_por_cargo_e_agenda(escolhas_com_candidatos)
        
        # Obter cabeçalho: prioriza o enviado no request; se vier vazio, usa o padrão do settings
        cabecalho_input = (cabecalho or '').strip()
        cabecalho_final = cabecalho_input if cabecalho_input else settings.RELATORIO_CABECALHO_PADRAO
        cabecalho_padrao = settings.RELATORIO_CABECALHO_PADRAO
        
        # Data atual para o relatório
        data_atual = timezone.now()
        
        if formato == 'xls' or formato == 'csv':
            filename = f'resultado_escolha_{processo_uuid}.xlsx'
            logger.info('Gerando Excel: %s', filename)
            response = self.render_to_xls(cargos_list, cabecalho_final, filename=filename)
            return response, cargos_list
        elif formato == 'pdf':
            filename = f'resultado_escolha_{processo_uuid}.pdf'
            logger.info('Gerando PDF: %s', filename)
            context = {
                'cargos': cargos_list,
                'cabecalho': cabecalho_final,
                'cabecalho_padrao': cabecalho_padrao,
                'data_atual': data_atual
            }
            response = self.render_to_pdf(
                self.TEMPLATE_NAME,
                context,
                filename=filename
            )
            return response, cargos_list
        else:
            logger.info('Gerando HTML')
            context = {
                'cargos': cargos_list,
                'cabecalho': cabecalho_final,
                'cabecalho_padrao': cabecalho_padrao,
                'data_atual': data_atual
            }
            response = render(
                request,
                self.TEMPLATE_NAME,
                context
            )
            return response, cargos_list
    
    def _extrair_numero_sessao(self, sessao: str) -> str:
        """
        Extrai apenas o número da sessão, removendo a palavra "Sessão" se presente.
        
        Args:
            sessao: String com a sessão (ex: "Sessão 4", "4", etc.)
            
        Returns:
            String com apenas o número da sessão ou '-' se não encontrar
        """
        if not sessao or sessao == '-':
            return '-'
        
        sessao_str = str(sessao).strip()
        
        # Remover a palavra "Sessão" (case insensitive)
        sessao_limpa = re.sub(r'^[Ss]ess[ãa]o\s*', '', sessao_str, flags=re.IGNORECASE)
        sessao_limpa = sessao_limpa.strip()
        
        # Extrair apenas números
        numeros = re.findall(r'\d+', sessao_limpa)
        if numeros:
            return numeros[0]
        
        return sessao_limpa if sessao_limpa else '-'
    
    def _agrupar_por_cargo_e_agenda(self, escolhas: list) -> list:
        """
        Agrupa escolhas por cargo da agenda e depois por agenda.
        
        Args:
            escolhas: Lista de escolhas com suas informações
            
        Returns:
            Lista de cargos (da agenda) com suas agendas e candidatos
        """
        cargos_dict = {}
        
        for escolha in escolhas:
            # Usar cargo da agenda (não do candidato)
            cargo_codigo = escolha.get('cargo_codigo', '') or ''
            cargo_descricao = escolha.get('cargo_descricao', '') or ''
            agenda_uuid = escolha.get('agenda_uuid')
            agenda_nome = escolha.get('agenda_nome', '-')
            agenda_data = escolha.get('agenda_data', '-')
            agenda_sessao = escolha.get('agenda_sessao', '-')
            # Processar sessão para extrair apenas o número
            sessao_numero = self._extrair_numero_sessao(agenda_sessao)
            
            # Se não tem descrição do cargo, usar código ou um valor padrão
            if not cargo_descricao:
                if cargo_codigo and cargo_codigo != '-':
                    cargo_descricao = f"Cargo {cargo_codigo}"
                else:
                    cargo_descricao = "Cargo não informado"
            
            # Criar chave única para a agenda (usando uuid ou nome+data)
            if agenda_uuid:
                agenda_chave = str(agenda_uuid)
            else:
                agenda_chave = f"{agenda_nome}_{agenda_data}_{agenda_sessao}"
            
            # Criar estrutura hierárquica: Cargo (da agenda) -> Agenda -> Candidatos
            if cargo_codigo not in cargos_dict:
                cargos_dict[cargo_codigo] = {
                    'codigo': cargo_codigo if cargo_codigo and cargo_codigo != '-' else '',
                    'descricao': cargo_descricao,
                    'agendas': {}
                }
            
            if agenda_chave not in cargos_dict[cargo_codigo]['agendas']:
                cargos_dict[cargo_codigo]['agendas'][agenda_chave] = {
                    'uuid': agenda_uuid,
                    'nome': agenda_nome,
                    'data': agenda_data,
                    'sessao': sessao_numero,  # Usar número processado
                    'candidatos': []
                }
            
            cargos_dict[cargo_codigo]['agendas'][agenda_chave]['candidatos'].append(escolha)
        
        # Converter para lista e ordenar
        cargos_list = []
        for cargo_codigo, cargo_data in cargos_dict.items():
            agendas_list = []
            for agenda_chave, agenda_data in cargo_data['agendas'].items():
                # Ordenar candidatos por classificação geral
                agenda_data['candidatos'].sort(key=lambda e: (
                    e['classificacao_geral'] if isinstance(e['classificacao_geral'], (int, float)) and e['classificacao_geral'] != '-' else float('inf')
                ))
                agendas_list.append(agenda_data)
            
            # Ordenar agendas por data e sessão (tratando sessão como número quando possível)
            agendas_list.sort(key=lambda a: (
                a['data'] if a['data'] != '-' else '',
                int(a['sessao']) if a['sessao'] != '-' and str(a['sessao']).isdigit() else (float('inf') if a['sessao'] != '-' else '')
            ))
            cargos_list.append({
                'codigo': cargo_data['codigo'],
                'descricao': cargo_data['descricao'],
                'agendas': agendas_list
            })
        
        # Ordenar cargos por descrição
        cargos_list.sort(key=lambda x: x['descricao'])
        
        return cargos_list
    
    def _imprimir_no_console(self, cargos_list: list):
        """
        Imprime o relatório no console para visualização.
        Estrutura: Cargo (da agenda) > Bloco (número da agenda) > Informações do candidato
        
        Args:
            cargos_list: Lista de cargos (da agenda) com suas agendas e candidatos
        """
        print("\n" + "="*100)
        print("RESULTADO DA ESCOLHA DE VAGAS - GERAL")
        print("="*100 + "\n")
        
        for cargo in cargos_list:
            cargo_descricao = cargo.get('descricao', '')
            print(f"\n{'='*100}")
            print(f"CARGO: {cargo_descricao}")
            print(f"{'='*100}\n")
            
            # Cabeçalho da tabela
            # Primeira coluna: "Qual a agenda" (bloco = número da agenda), depois informações do candidato
            print(f"{'Agenda':<30} {'Class. geral':<15} {'Class. Def.':<15} {'Class. NNA':<15} {'NOME':<40} {'R.G.':<20} {'CPF':<15} {'ESCOLHA':<10}")
            print("-" * 100)
            
            # Iterar pelas agendas e numerá-las (bloco 1, 2, 3, etc.)
            bloco_numero = 1
            for agenda in cargo.get('agendas', []):
                agenda_nome = agenda.get('nome', '-')
                agenda_data = agenda.get('data', '-')
                agenda_sessao = agenda.get('sessao', '-')
                
                # Formatar informações da agenda para exibição
                if agenda_data and agenda_data != '-':
                    # Formatar data se necessário
                    if isinstance(agenda_data, str) and 'T' in agenda_data:
                        # Se for formato ISO com timestamp, pegar apenas a data
                        agenda_data_formatada = agenda_data.split('T')[0]
                    else:
                        agenda_data_formatada = str(agenda_data)
                else:
                    agenda_data_formatada = '-'
                agenda_label = f"Bloco {bloco_numero}"
                if agenda_nome and agenda_nome != '-':
                    agenda_label += f" - {agenda_nome}"
                if agenda_data_formatada and agenda_data_formatada != '-':
                    agenda_label += f" ({agenda_data_formatada}"
                    if agenda_sessao and agenda_sessao != '-':
                        agenda_label += f" / {agenda_sessao}"
                    agenda_label += ")"
                
                # Dados dos candidatos desta agenda
                for candidato in agenda.get('candidatos', []):
                    classificacao_geral = candidato.get('classificacao_geral', '-')
                    classificacao_def = candidato.get('classificacao_def', '-')
                    classificacao_nna = candidato.get('classificacao_nna', '-')
                    nome = candidato.get('nome', '-')
                    rg = candidato.get('rg', '-')
                    cpf = candidato.get('cpf', '-')
                    escolha_valor = candidato.get('escolha', '-')
                    
                    # Formatar valores para exibição
                    class_geral_str = str(classificacao_geral) if classificacao_geral != '-' else '-'
                    class_def_str = str(classificacao_def) if classificacao_def != '-' else '-'
                    class_nna_str = str(classificacao_nna) if classificacao_nna != '-' else '-'
                    
                    # Bloco = número da agenda (1, 2, 3, etc.) exibido como identificação da agenda
                    print(f"{agenda_label:<30} {class_geral_str:<15} {class_def_str:<15} {class_nna_str:<15} {nome:<40} {rg:<20} {cpf:<15} {escolha_valor:<10}")
                
                # Incrementar bloco para próxima agenda
                bloco_numero += 1
            
            print()
        
        print("\n" + "="*100)
        print("FIM DO RELATÓRIO")
        print("="*100 + "\n")
    
    def render_to_xls(self, cargos_list, cabecalho, filename='resultado_escolha.xlsx'):
        """
        Gera um arquivo Excel (XLSX) mantendo a estrutura hierárquica do HTML.
        
        Args:
            cargos_list: Lista de cargos com suas agendas e candidatos (estrutura hierárquica)
            cabecalho: Texto do cabeçalho do relatório
            filename: Nome do arquivo Excel gerado
        
        Returns:
            HttpResponse com o arquivo Excel gerado
        """
        if not OPENPYXL_AVAILABLE:
            raise ImportError(
                "openpyxl não está instalado. Instale com: pip install openpyxl>=3.1.0"
            )
        
        try:
            wb = Workbook()
            ws = wb.active
            ws.title = "Resultado da Escolha"
            
            cargo_fill = PatternFill(start_color="667eea", end_color="667eea", fill_type="solid")
            table_header_fill = PatternFill(start_color="ECF0F1", end_color="ECF0F1", fill_type="solid")
            cargo_font = Font(bold=True, color="FFFFFF", size=12)
            header_font = Font(bold=True, size=10)
            normal_font = Font(size=10)
            title_font = Font(bold=True, size=14)
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            center_align = Alignment(horizontal='center', vertical='center')
            center_wrap_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
            left_align = Alignment(horizontal='left', vertical='center')
            
            row = 1
            
            if cabecalho:
                ws.merge_cells(f'A{row}:H{row}')
                cell = ws[f'A{row}']
                cabecalho_texto = self.processar_cabecalho_html(cabecalho)
                cell.value = cabecalho_texto
                cell.font = title_font
                cell.alignment = center_wrap_align
                row += 2
            
            # Título do relatório
            ws.merge_cells(f'A{row}:H{row}')
            cell = ws[f'A{row}']
            cell.value = "RESULTADO DA ESCOLHA DE VAGAS - GERAL"
            cell.font = Font(bold=True, size=16)
            cell.alignment = center_align
            row += 1
            
            # Data do relatório
            ws.merge_cells(f'A{row}:H{row}')
            cell = ws[f'A{row}']
            data_atual = timezone.now()
            # Formatar data em português
            meses_pt = {
                1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril',
                5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto',
                9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'
            }
            mes_nome = meses_pt.get(data_atual.month, '')
            data_formatada = f"{data_atual.day} de {mes_nome} de {data_atual.year}"
            cell.value = f"REALIZADO EM: {data_formatada}"
            cell.font = Font(size=12)
            cell.alignment = center_align
            row += 2
            
            for cargo in cargos_list:
                cargo_descricao = cargo.get('descricao', '')
                
                # Cabeçalho do cargo
                ws.merge_cells(f'A{row}:H{row}')
                cell = ws[f'A{row}']
                cell.value = cargo_descricao
                cell.font = cargo_font
                cell.fill = cargo_fill
                cell.alignment = left_align
                row += 1
                
                # Cabeçalhos da tabela
                headers = ['Bloco', 'Geral', 'NNA', 'Def.', 'NOME', 'R.G.', 'CPF', 'ESCOLHA']
                for col, header in enumerate(headers, start=1):
                    cell = ws.cell(row=row, column=col)
                    cell.value = header
                    cell.fill = table_header_fill
                    cell.font = header_font
                    cell.alignment = center_align
                    cell.border = border
                row += 1
                
                # Dados dos candidatos
                for agenda in cargo.get('agendas', []):
                    sessao = agenda.get('sessao', '-')
                    for candidato in agenda.get('candidatos', []):
                        ws.cell(row=row, column=1).value = sessao
                        ws.cell(row=row, column=2).value = candidato.get('classificacao_geral', '-')
                        ws.cell(row=row, column=3).value = candidato.get('classificacao_nna', '-')
                        ws.cell(row=row, column=4).value = candidato.get('classificacao_def', '-')
                        ws.cell(row=row, column=5).value = candidato.get('nome', '-')
                        ws.cell(row=row, column=6).value = candidato.get('rg', '-')
                        ws.cell(row=row, column=7).value = candidato.get('cpf', '-')
                        ws.cell(row=row, column=8).value = candidato.get('escolha', '-')
                        
                        # Aplicar formatação
                        for col in range(1, 9):
                            cell = ws.cell(row=row, column=col)
                            cell.border = border
                            cell.font = normal_font
                            if col in [1, 2, 3, 4, 8]:  # Bloco, Geral, NNA, Def., ESCOLHA
                                cell.alignment = center_align
                            else:  # NOME, R.G., CPF
                                cell.alignment = left_align
                        
                        row += 1
                
                row += 1
            
            # Ajustar larguras das colunas
            column_widths = {
                'A': 10,  # Bloco
                'B': 12,  # Geral
                'C': 12,  # NNA
                'D': 12,  # Def.
                'E': 40,  # NOME
                'F': 18,  # R.G.
                'G': 15,  # CPF
                'H': 10,  # ESCOLHA
            }
            
            for col_letter, width in column_widths.items():
                ws.column_dimensions[col_letter].width = width
            
            buffer = BytesIO()
            wb.save(buffer)
            buffer.seek(0)
            
            response = HttpResponse(
                buffer.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as exc:
            logger.error('Erro ao gerar Excel: %s', exc, exc_info=True)
            raise

