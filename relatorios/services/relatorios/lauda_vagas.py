"""
Implementação concreta do relatório de Lauda de Vagas.
"""
import logging
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from io import BytesIO
from relatorios.services.base.relatorio_base import RelatorioBase
from relatorios.services.escolhas_api_service import EscolhasService

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

logger = logging.getLogger(__name__)

class LaudaVagas(RelatorioBase):
    """
    Classe concreta responsável por gerar o relatório de Lauda de Vagas.
    """
    
    TEMPLATE_NAME = 'relatorios/vagas_escolas.html'
    
    def __init__(self):
        """Inicializa o service com as dependências necessárias."""
        self.escolhas_service = EscolhasService(base_url=settings.ESCOLHAS_API_URL)
    
    def gerar(self, processo_uuid: str, request, formato: str = 'html', cabecalho: str = ''):
        """
        Gera o relatório de Lauda de Vagas.
        
        Args:
            processo_uuid: UUID do processo de convocação
            request: Objeto request do Django
            formato: Formato do relatório ('html', 'pdf' ou 'xls')
            cabecalho: Texto do cabeçalho do relatório (opcional)
        
        Returns:
            Tupla (HttpResponse, dados) onde:
            - HttpResponse: resposta com o relatório gerado (HTML, PDF ou XLS)
            - dados: estrutura de dados do relatório (cargos_list) para salvar no banco
        """
        # Buscar vagas das escolas do microserviço de escolhas
        try:
            vagas_escolas = self.escolhas_service.buscar_vagas_escolas(
                processo_uuid=str(processo_uuid) if processo_uuid else '',
            )

        except Exception as exc:
            logger.error('Falha ao buscar vagas de escolas da API externa: %s', exc)
            raise
        
        vagas = vagas_escolas.json().get('vagas', [])
        
        vagas_agrupadas = self._agrupar_vagas(vagas)
        
        cargos_list = self._preparar_dados_template(vagas_agrupadas)

        # Obter cabeçalho: prioriza o enviado no request; se vier vazio, usa o padrão do settings
        cabecalho_input = (cabecalho or '').strip()
        cabecalho_final = cabecalho_input if cabecalho_input else settings.RELATORIO_CABECALHO_PADRAO
        cabecalho_padrao = settings.RELATORIO_CABECALHO_PADRAO
        
        if formato == 'xls':
            filename = f'relatorio_vagas_{processo_uuid}.xlsx'
            logger.info('Gerando Excel: %s', filename)
            response = self.render_to_xls(cargos_list, cabecalho_final, filename=filename)
            return response, cargos_list
        
        elif formato == 'pdf':
            filename = f'relatorio_vagas_{processo_uuid}.pdf'
            logger.info('Gerando PDF: %s', filename)
            context = {
                'cargos': cargos_list,
                'cabecalho': cabecalho_final,
                'cabecalho_padrao': cabecalho_padrao
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
                'cabecalho_padrao': cabecalho_padrao
            }
            response = render(
                request,
                self.TEMPLATE_NAME,
                context
            )
            return response, cargos_list
    
    def _agrupar_vagas(self, vagas: list) -> dict:
        """
        Agrupa vagas por cargo_codigo e depois por DRE codigo.
        
        Args:
            vagas: Lista de vagas
        
        Returns:
            Dicionário agrupado por cargo e DRE
        """
        vagas_agrupadas = {}
        for vaga in vagas:
            cargo_codigo = vaga.get('cargo_codigo')
            dre_codigo = vaga.get('escola', {}).get('dre', {}).get('codigo')
            
            if cargo_codigo not in vagas_agrupadas:
                vagas_agrupadas[cargo_codigo] = {}
            
            if dre_codigo not in vagas_agrupadas[cargo_codigo]:
                vagas_agrupadas[cargo_codigo][dre_codigo] = []
            
            vagas_agrupadas[cargo_codigo][dre_codigo].append(vaga)
        
        return vagas_agrupadas
    
    def _preparar_dados_template(self, vagas_agrupadas: dict) -> list:
        """
        Prepara a estrutura de dados para o template.
        
        Args:
            vagas_agrupadas: Dicionário com vagas agrupadas por cargo e DRE
        
        Returns:
            Lista de cargos com suas DREs e vagas
        """
        cargos_list = []
        for cargo_codigo, dres in vagas_agrupadas.items():            
            primeira_vaga = None
            for dre_codigo, vagas_list in dres.items():
                if vagas_list:
                    primeira_vaga = vagas_list[0]
                    break
            
            if primeira_vaga:
                dres_list = []
                for dre_codigo, vagas_list in dres.items():
                    if vagas_list:
                        primeira_vaga_dre = vagas_list[0]
                        dres_list.append({
                            'codigo': dre_codigo,
                            'nome': primeira_vaga_dre.get('escola', {}).get('dre', {}).get('nome', ''),
                            'vagas': vagas_list
                        })
                
                cargos_list.append({
                    'codigo': cargo_codigo,
                    'descricao': primeira_vaga.get('cargo_descricao', ''),
                    'dres': dres_list
                })
        
        return cargos_list
    
    def render_to_xls(self, cargos_list, cabecalho, filename='relatorio.xlsx'):
        """
        Gera um arquivo Excel (XLSX) mantendo a estrutura hierárquica do HTML.
        Formato baseado na estrutura de comunicado oficial.
        
        Args:
            cargos_list: Lista de cargos com suas DREs e vagas (estrutura hierárquica)
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
            ws.title = "Relatório de Vagas"
            
            cargo_fill = PatternFill(start_color="667eea", end_color="667eea", fill_type="solid")
            dre_fill = PatternFill(start_color="34495e", end_color="34495e", fill_type="solid")
            table_header_fill = PatternFill(start_color="ECF0F1", end_color="ECF0F1", fill_type="solid")
            cargo_font = Font(bold=True, color="FFFFFF", size=12)
            dre_font = Font(bold=True, color="FFFFFF", size=11)
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
                ws.merge_cells(f'A{row}:D{row}')
                cell = ws[f'A{row}']
                cabecalho_texto = self.processar_cabecalho_html(cabecalho)
                cell.value = cabecalho_texto
                cell.font = title_font
                cell.alignment = center_wrap_align
                row += 2
            
            for cargo in cargos_list:
                cargo_descricao = cargo.get('descricao', '')
                
                ws.merge_cells(f'A{row}:D{row}')
                cell = ws[f'A{row}']
                cell.value = f"Cargo: {cargo_descricao}"
                cell.font = cargo_font
                cell.fill = cargo_fill
                cell.alignment = left_align
                row += 1
                
                for dre in cargo.get('dres', []):
                    dre_nome = dre.get('nome', '')
                    
                    ws.merge_cells(f'A{row}:D{row}')
                    cell = ws[f'A{row}']
                    cell.value = f"DRE - {dre_nome}"
                    cell.font = dre_font
                    cell.fill = dre_fill
                    cell.alignment = left_align
                    row += 1
                    
                    headers = ['Tipo de unidade', 'Unidade', 'Vagas Definitivas', 'Vagas Precárias']
                    for col, header in enumerate(headers, start=1):
                        cell = ws.cell(row=row, column=col)
                        cell.value = header
                        cell.fill = table_header_fill
                        cell.font = header_font
                        cell.alignment = center_align
                        cell.border = border
                    row += 1
                    
                    for vaga in dre.get('vagas', []):
                        escola = vaga.get('escola', {})
                        
                        ws.cell(row=row, column=1).value = escola.get('tipo_ue', '-')
                        ws.cell(row=row, column=2).value = escola.get('nome_oficial', '-')
                        ws.cell(row=row, column=3).value = vaga.get('vagas_definitivas', 0)
                        ws.cell(row=row, column=4).value = vaga.get('vagas_precarias', 0)
                        
                        for col in range(1, 5):
                            cell = ws.cell(row=row, column=col)
                            cell.border = border
                            cell.font = normal_font
                            if col in [3, 4]:  
                                cell.alignment = center_align
                            else:
                                cell.alignment = left_align
                        
                        row += 1
                                            
                    row += 1

                row += 1
            
            
            column_widths = {
                'A': 20,  # Tipo de Unidade
                'B': 60,  # Unidade
                'C': 20,  # Vagas Definitivas
                'D': 20,  # Vagas Precárias
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

