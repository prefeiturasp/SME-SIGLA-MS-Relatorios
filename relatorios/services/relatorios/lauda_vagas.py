"""
Implementação concreta do relatório de Lauda de Vagas.
"""
import logging
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from io import BytesIO
import tempfile
import os
import requests
from relatorios.services.base.relatorio_base import RelatorioBase
from relatorios.services.escolhas_api_service import EscolhasService
from relatorios.utils import convert_uuids_to_strings

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.drawing.image import Image as XLImage
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

logger = logging.getLogger(__name__)

class LaudaVagas(RelatorioBase):
    """
    Classe concreta responsável por gerar o relatório de Lauda de Vagas.
    """
    
    TEMPLATE_NAME = 'relatorios/vagas_escolas.html'
    
    def __init__(self, **kwargs):
        """Inicializa o service com as dependências necessárias."""
        super().__init__(**kwargs)
        self.escolhas_service = EscolhasService(base_url=settings.ESCOLHAS_API_URL)
    
    def gerar(self, processo_uuid: str, request, formato: str = 'html', cabecalho: str = '', **kwargs):
        """
        Gera o relatório de Lauda de Vagas.
        
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
        # Converter todos os UUIDs para strings para garantir serialização JSON
        cargos_list = convert_uuids_to_strings(cargos_list)
        # Obter cabeçalho: prioriza o enviado no request; se vier vazio, usa o padrão do settings
        cabecalho_final = self.context['cabecalho_padrao'] if self.context['usar_cabecalho_padrao'] else self.context['cabecalho']
        logo_url = request.build_absolute_uri(self.parametrizacao.logo.url) if self.parametrizacao and self.parametrizacao.logo else ''
        self.context.update({
            'logo_url': logo_url,
            'cargos': cargos_list,
        })
        if formato == 'xls' or formato == 'csv':
            filename = f'relatorio_vagas_{processo_uuid}.xlsx'
            logger.info('Gerando Excel: %s', filename)
            response = self.render_to_xls(
                context=self.context,
                filename=filename
            )
            return response, cargos_list
        elif formato == 'docx' or formato == 'doc':
            filename = f'relatorio_vagas_{processo_uuid}.docx'
            logger.info('Gerando Word: %s', filename)
            response = self.render_to_docx(
                cargos_list,
                cabecalho_final,
                self.context['texto_final'],
                filename=filename
            )
            return response, cargos_list
        elif formato == 'pdf':
            filename = f'relatorio_vagas_{processo_uuid}.pdf'
            logger.info('Gerando PDF: %s', filename)
            self.context.update({
                'is_pdf': True,
                'cargos': cargos_list,
            })
            response = self.render_to_pdf(
                self.TEMPLATE_NAME,
                self.context,
                filename=filename
            )
            return response, cargos_list
        else:
            logger.info('Gerando HTML')
            self.context["cargos"] = cargos_list
            response = render(
                request,
                self.TEMPLATE_NAME,
                self.context
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
    
    def render_to_xls(self, context={}, filename='relatorio.xlsx'):
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
            temp_image_paths = []
            # Inserir logotipo no topo, se disponível
            logo_url = (context or self.context).get('logo_url') if context or self.context else ''
            if context.get('usar_logotipo') and logo_url:
                image_path = None
                try:
                    if logo_url.startswith('http://') or logo_url.startswith('https://'):
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpf:
                            resp = requests.get(logo_url, timeout=15)
                            resp.raise_for_status()
                            tmpf.write(resp.content)
                            image_path = tmpf.name
                            temp_image_paths.append(image_path)
                    elif os.path.exists(logo_url):
                        image_path = logo_url
                    if image_path:
                        img = XLImage(image_path)
                        # opcional: ajustar tamanho
                        try:
                            # Reduz o tamanho da imagem
                            img.width = 220
                            img.height = 90
                        except Exception:
                            pass
                        # Aproxima o alinhamento central ancorando em uma coluna intermediária
                        # Como a planilha usa 4 colunas (A:D), ancorar em B1 fica visualmente centralizado
                        ws.add_image(img, 'B1')
                        # Avança algumas linhas para não sobrepor conteúdo
                        row = max(row, 8)
                except Exception as exc:
                    logger.warning('Não foi possível inserir o logotipo no XLS: %s', exc)

            cabecalho = self.context['cabecalho_padrao'] if self.context['usar_cabecalho_padrao'] else self.context['cabecalho']
            if cabecalho:
                ws.merge_cells(f'A{row}:D{row}')
                cell = ws[f'A{row}']
                cabecalho_texto = self.processar_cabecalho_html(cabecalho)
                cell.value = cabecalho_texto
                cell.font = title_font
                cell.alignment = center_wrap_align
                row += 2
            
            for cargo in self.context['cargos']:
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

            # Adiciona texto final ao término do relatório, se houver
            texto_final = self.context.get('texto_final')
            if texto_final:
                row += 1
                ws.merge_cells(f'A{row}:D{row}')
                cell = ws[f'A{row}']
                cell.value = self.processar_cabecalho_html(texto_final)
                cell.font = normal_font
                cell.alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)

            buffer = BytesIO()
            wb.save(buffer)
            buffer.seek(0)
            # Limpar temporários de imagem
            for p in temp_image_paths:
                try:
                    if os.path.exists(p):
                        os.unlink(p)
                except Exception:
                    pass
            
            response = HttpResponse(
                buffer.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as exc:
            logger.error('Erro ao gerar Excel: %s', exc, exc_info=True)
            raise
    
    def render_to_docx(self, cargos_list, cabecalho, texto_final, filename='relatorio_vagas.docx'):
        """
        Gera um arquivo Word (DOCX) mantendo a estrutura hierárquica do Excel.
        Formato baseado na estrutura de comunicado oficial - EXATAMENTE IGUAL AO XLS.
        
        Args:
            cargos_list: Lista de cargos com suas DREs e vagas (estrutura hierárquica)
            cabecalho: Texto do cabeçalho do relatório
            texto_final: Texto final do relatório
            filename: Nome do arquivo Word gerado
        
        Returns:
            HttpResponse com o arquivo Word gerado
        """
        if not DOCX_AVAILABLE:
            raise ImportError(
                "python-docx não está instalado. Instale com: pip install python-docx>=1.1.0"
            )
        
        try:
            doc = Document()
            
            # Configurar margens da página
            sections = doc.sections
            for section in sections:
                section.top_margin = Inches(1)
                section.bottom_margin = Inches(1)
                section.left_margin = Inches(1)
                section.right_margin = Inches(1)
            
            # Cores (em RGB)
            cargo_color = RGBColor(102, 126, 234)  # #667eea
            dre_color = RGBColor(52, 73, 94)  # #34495e
            table_header_color = RGBColor(236, 240, 241)  # #ECF0F1
            
            # Cabeçalho
            if cabecalho:
                cabecalho_texto = self.processar_cabecalho_html(cabecalho)
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(cabecalho_texto)
                run.font.size = Pt(14)
                run.font.bold = True
                doc.add_paragraph()
            
            # Processar cargos
            for cargo in cargos_list:
                cargo_descricao = cargo.get('descricao', '')
                
                # Título do cargo
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run = p.add_run(f"Cargo: {cargo_descricao}")
                run.font.size = Pt(12)
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
                p_pr = p._element.get_or_add_pPr()
                existing_shd = p_pr.find(qn('w:shd'))
                if existing_shd is not None:
                    p_pr.remove(existing_shd)
                shading_elm = OxmlElement('w:shd')
                shading_elm.set(qn('w:fill'), '667eea')
                shading_elm.set(qn('w:val'), 'clear')
                p_pr.append(shading_elm)
                
                for dre in cargo.get('dres', []):
                    dre_nome = dre.get('nome', '')
                    
                    # Título da DRE
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    run = p.add_run(f"DRE - {dre_nome}")
                    run.font.size = Pt(11)
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(255, 255, 255)
                    p_pr = p._element.get_or_add_pPr()
                    existing_shd = p_pr.find(qn('w:shd'))
                    if existing_shd is not None:
                        p_pr.remove(existing_shd)
                    shading_elm = OxmlElement('w:shd')
                    shading_elm.set(qn('w:fill'), '34495e')
                    shading_elm.set(qn('w:val'), 'clear')
                    p_pr.append(shading_elm)
                    
                    # Criar tabela
                    headers = ['Tipo de unidade', 'Unidade', 'Vagas Definitivas', 'Vagas Precárias']
                    table = doc.add_table(rows=1, cols=len(headers))
                    table.style = 'Light Grid Accent 1'
                    
                    # Cabeçalho da tabela
                    header_cells = table.rows[0].cells
                    for i, header in enumerate(headers):
                        cell = header_cells[i]
                        cell.text = header
                        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                        cell.paragraphs[0].runs[0].font.bold = True
                        cell.paragraphs[0].runs[0].font.size = Pt(10)
                        tc_pr = cell._element.get_or_add_tcPr()
                        existing_shd = tc_pr.find(qn('w:shd'))
                        if existing_shd is not None:
                            tc_pr.remove(existing_shd)
                        shading_elm = OxmlElement('w:shd')
                        shading_elm.set(qn('w:fill'), 'ECF0F1')
                        shading_elm.set(qn('w:val'), 'clear')
                        tc_pr.append(shading_elm)
                    
                    # Dados das vagas
                    for vaga in dre.get('vagas', []):
                        escola = vaga.get('escola', {})
                        row_cells = table.add_row().cells
                        
                        row_cells[0].text = escola.get('tipo_ue', '-')
                        row_cells[1].text = escola.get('nome_oficial', '-')
                        row_cells[2].text = str(vaga.get('vagas_definitivas', 0))
                        row_cells[3].text = str(vaga.get('vagas_precarias', 0))
                        
                        # Alinhamento
                        for i, cell in enumerate(row_cells):
                            if i in [2, 3]:
                                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                            else:
                                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
                            cell.paragraphs[0].runs[0].font.size = Pt(10)
                    
                    doc.add_paragraph()
            
            if texto_final:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run = p.add_run(self.processar_cabecalho_html(texto_final))
                run.font.size = Pt(10)
                doc.add_paragraph()

            # Salvar em buffer
            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            
            response = HttpResponse(
                buffer.read(),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as exc:
            logger.error('Erro ao gerar Word: %s', exc, exc_info=True)
            raise

