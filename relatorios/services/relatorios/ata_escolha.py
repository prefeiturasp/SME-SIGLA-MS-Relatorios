"""
Implementação concreta do relatório de Ata de Escolha.
Baseado no padrão da Ata de Convocação, mas com informações da escola escolhida.
"""
import json
import logging
import re
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from io import BytesIO
import tempfile
import os
from relatorios.services.base.relatorio_base import RelatorioBase
from relatorios.services.ata_escolha_service import AtaEscolhaService
from relatorios.models import ConfiguracaoRelatorio, Parametrizacao

try:
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

logger = logging.getLogger(__name__)


class AtaEscolha(RelatorioBase):
    """
    Classe concreta responsável por gerar o relatório de Ata de Escolha.
    """
    
    TEMPLATE_NAME = 'relatorios/ata_escolha.html'
    
    def __init__(self, **kwargs):
        """Inicializa o service com as dependências necessárias."""
        super().__init__(**kwargs)
        self.ata_service = AtaEscolhaService(
            candidatos_base_url=settings.CANDIDATOS_API_URL,
            processo_base_url=settings.CONVOCACAO_API_URL,
            agendas_base_url=settings.AGENDAS_API_URL,
            escolhas_base_url=settings.ESCOLHAS_API_URL
        )

    def _preencher_template(self, cabecalho_capa, dados):
        # Regex para encontrar qualquer coisa entre [[ ]]
        pattern = re.compile(r'\[\[(.*?)\]\]')
        
        def replace_func(match):
            chave = match.group(1) # Pega o que está dentro de [[ ]]
            return str(dados.get(chave, f"[[ERRO: {chave} NÃO ENCONTRADO]]"))

        return pattern.sub(replace_func, cabecalho_capa)
    
    def gerar(self, processo_uuid: str, request, formato: str = 'html', **kwargs):
        """
        Gera o relatório de Ata de Escolha.
        
        Args:
            processo_uuid: UUID do processo de convocação
            request: Objeto request do Django
            formato: Formato do relatório ('html', 'pdf' ou 'xls')
            cabecalho: Texto do cabeçalho do relatório (opcional)
        
        Returns:
            Tupla (HttpResponse, dados) onde:
            - HttpResponse: resposta com o relatório gerado (HTML, PDF ou XLS)
            - dados: estrutura de dados do relatório para salvar no banco
        """
        # Processar ata de escolha usando o serviço
        try:
            dados_ata = self.ata_service.processar_ata_escolha(
                processo_uuid=str(processo_uuid) if processo_uuid else ''
            )

        except Exception as exc:
            logger.error('Falha ao processar ata de escolha: %s', exc)
            raise
        mostrar_capa_ata = True
        datas_preencher_tempalte = {
            "cargo": dados_ata.get('cargos', [])[0]["cargo_nome"],
            "tipos_vagas": "PRECÁRIAS/DEFINITIVAS",
        }
        cabecalho_capa_ata = self._preencher_template(self.context['cabecalho_capa_ata'], datas_preencher_tempalte)
        logo_url = request.build_absolute_uri(self.parametrizacao.logo.url) if self.parametrizacao and self.parametrizacao.logo else ''
        context_data = self.context.copy()
        context_data.update({
            'cargos': dados_ata.get('cargos', []),
            'candidatos_sep_cargo': dados_ata.get('candidatos_sep_cargo', {}),
            'cabecalho_capa_ata': cabecalho_capa_ata,
            'mostrar_capa_ata': False,
            'escolhas_totais_por_tipo': dados_ata.get('escolhas_totais_por_tipo', {}),
            'logo_url': logo_url,
            'is_pdf': False,
        })

        if formato == 'docx' or formato == 'doc':
            filename = f'ata_escolha_{processo_uuid}.docx'
            logger.info('Gerando Word (via PDF -> DOCX): %s', filename)
            try:
                from pdf2docx import parse as pdf_to_docx_parse
            except Exception as exc:
                logger.error('pdf2docx não está instalado ou falhou ao importar: %s', exc)
                raise ImportError("pdf2docx não está instalado. Instale com: pip install pdf2docx")

            context_data['is_pdf'] = True
            context_data['mostrar_capa_ata'] = True
            pdf_response = self.render_to_pdf(self.TEMPLATE_NAME, context_data, filename=f'ata_escolha_{processo_uuid}.pdf')
            pdf_bytes = pdf_response.content

            # 2) Grava PDF em arquivo temporário e converte para DOCX
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    pdf_path = os.path.join(tmpdir, 'input.pdf')
                    docx_path = os.path.join(tmpdir, 'output.docx')
                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_bytes)
                    # Converter PDF -> DOCX
                    pdf_to_docx_parse(pdf_path, docx_path)
                    with open(docx_path, 'rb') as f:
                        docx_content = f.read()
            except Exception as exc:
                logger.error('Falha ao converter PDF em DOCX: %s', exc, exc_info=True)
                raise

            # 3) Retorna o DOCX como resposta
            response = HttpResponse(
                docx_content,
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response, dados_ata
        elif formato == 'pdf':
            context_data['mostrar_capa_ata'] = True
            filename = f'ata_escolha_{processo_uuid}.pdf'
            logger.info('Gerando PDF: %s', filename)
            context_data['is_pdf'] = True
            response = self.render_to_pdf(self.TEMPLATE_NAME, context_data, filename=filename)
            return response, dados_ata
        elif formato in ('xls', 'xlsx'):
            filename = f'ata_escolha_{processo_uuid}.xlsx'
            logger.info('Gerando XLS: %s', filename)
            response = self._render_xls(
                dados_ata.get('cargos', []),
                context_data['cabecalho'],
                filename=filename
            )
            return response, dados_ata
        elif formato == 'html':
            print(dados_ata.get('escolhas_totais_por_tipo', {}))
            logger.info('Gerando HTML')
            response = render(request, self.TEMPLATE_NAME, context_data)
            return response, dados_ata
        else:
            # Retornar JSON por padrão
            response = JsonResponse(dados_ata, safe=False, json_dumps_params={'indent': 2, 'ensure_ascii': False})
        
        return response, dados_ata
    
    def render_to_docx(self, cargos_list, cabecalho, filename='ata_escolha.docx'):
        """
        Gera um arquivo Word (DOCX) mantendo a estrutura hierárquica do HTML.
        
        Args:
            cargos_list: Lista de cargos com suas sessões e candidatos
            cabecalho: Texto do cabeçalho do relatório
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
                section.top_margin = Inches(0.5)
                section.bottom_margin = Inches(0.5)
                section.left_margin = Inches(0.5)
                section.right_margin = Inches(0.5)
                section.orientation = 1  # Landscape
            
            # Cores (em RGB)
            sessao_color = RGBColor(52, 73, 94)  # #34495e
            cargo_color = RGBColor(102, 126, 234)  # #667eea
            table_header_color = RGBColor(236, 240, 241)  # #ECF0F1
            
            # Cabeçalho
            if cabecalho:
                cabecalho_texto = self.processar_cabecalho_html(cabecalho)
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.add_run(cabecalho_texto)
                run.font.size = Pt(12)
                run.font.bold = True
                doc.add_paragraph()
            
            # Título
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run("ATA DE ESCOLHA")
            run.font.size = Pt(14)
            run.font.bold = True
            doc.add_paragraph()
            
            # Lei de referência
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run("")
            run.font.size = Pt(10)
            run.font.italic = True
            doc.add_paragraph()
            
            # Processar cargos e sessões
            for cargo in cargos_list:
                cargo_nome = cargo.get('cargo_nome', '')
                
                for sessao in cargo.get('sessoes', []):
                    # Cabeçalho da sessão
                    numero_sessao = sessao.get('numero_sessao', '')
                    horario_formatado = sessao.get('horario_formatado', '')
                    sessao_texto = f"{numero_sessao}ª SESSÃO"
                    if horario_formatado:
                        sessao_texto += f" - Horário: {horario_formatado}"
                    
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    run = p.add_run(sessao_texto)
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
                    
                    # Cabeçalho do cargo
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    run = p.add_run(f"CARGO: {cargo_nome}")
                    run.font.size = Pt(11)
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
                    
                    # Criar tabela
                    headers = ['Class. Geral', 'Class. Def.', 'Class. NNA', 'RF', 'RG', 'CPF', 'Nome', 
                              'Código EOL', 'DRE', 'Tipo Unidade', 'Unidade Escolhida', 'Tipo Vaga', 'Assinatura']
                    table = doc.add_table(rows=1, cols=len(headers))
                    table.style = 'Light Grid Accent 1'
                    
                    # Cabeçalho da tabela
                    header_cells = table.rows[0].cells
                    for i, header in enumerate(headers):
                        cell = header_cells[i]
                        cell.text = header
                        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER if i < 6 or i >= 7 else WD_ALIGN_PARAGRAPH.LEFT
                        cell.paragraphs[0].runs[0].font.bold = True
                        cell.paragraphs[0].runs[0].font.size = Pt(8)
                        tc_pr = cell._element.get_or_add_tcPr()
                        existing_shd = tc_pr.find(qn('w:shd'))
                        if existing_shd is not None:
                            tc_pr.remove(existing_shd)
                        shading_elm = OxmlElement('w:shd')
                        shading_elm.set(qn('w:fill'), 'ECF0F1')
                        shading_elm.set(qn('w:val'), 'clear')
                        tc_pr.append(shading_elm)
                    
                    # Dados dos candidatos
                    for candidato in sessao.get('candidatos', []):
                        row_cells = table.add_row().cells
                        
                        # Extrair dados do candidato
                        candidato_obj = candidato.get('candidato', {}) if isinstance(candidato.get('candidato'), dict) else {}
                        
                        # Classificações
                        row_cells[0].text = '-' if str(candidato.get('classificacao', '-')) == 'None' else str(candidato.get('classificacao', '-'))
                        row_cells[1].text = '-' if str(candidato.get('classificacao_pcd', '-')) == 'None' else str(candidato.get('classificacao_pcd', '-'))
                        row_cells[2].text = '-' if str(candidato.get('classificacao_nna', '-')) == 'None' else str(candidato.get('classificacao_nna', '-'))
                        
                        # RF, RG, CPF
                        # RF = registro_funcional (do model candidato)
                        rf = candidato.get('rf', '') or (candidato_obj.get('registro_funcional', '') if isinstance(candidato_obj, dict) else '') or '-'
                        rg = candidato.get('rg', '') or (candidato_obj.get('rg', '') if isinstance(candidato_obj, dict) else '') or '-'
                        cpf = candidato.get('cpf', '') or (candidato_obj.get('cpf', '') if isinstance(candidato_obj, dict) else '') or '-'
                        row_cells[3].text = str(rf)
                        row_cells[4].text = str(rg)
                        row_cells[5].text = str(cpf)
                        
                        # Nome
                        status_especial = candidato.get('status_especial', '')
                        if status_especial:
                            row_cells[6].text = status_especial
                        else:
                            nome = candidato.get('nome', '') or (candidato_obj.get('nome', 'N/A') if isinstance(candidato_obj, dict) else 'N/A')
                            row_cells[6].text = nome
                        
                        # Dados da escola escolhida
                        row_cells[7].text = str(candidato.get('codigo_eol', '-') or '-')
                        row_cells[8].text = str(candidato.get('dre_codigo', '-') or '-')
                        row_cells[9].text = str(candidato.get('tipo_unidade', '-') or '-')
                        row_cells[10].text = str(candidato.get('nome_escola_escolhida', '-') or '-')
                        row_cells[11].text = str(candidato.get('tipo_vaga', '-') or '-')
                        row_cells[12].text = str(candidato.get('assinatura', 'Não Escolha') or 'Não Escolha')

                        # Alinhamento
                        for i, cell in enumerate(row_cells):
                            if i < 6 or (i >= 7 and i < 12):  # Colunas centralizadas (exceto Nome e Unidade Escolhida)
                                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                            else:  # Nome e Unidade Escolhida
                                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
                            cell.paragraphs[0].runs[0].font.size = Pt(8)
                    
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

    def _render_xls(self, cargos_list, cabecalho, filename='ata_escolha.xlsx'):
        """
        Gera um arquivo Excel (XLSX) com a estrutura da Ata de Escolha.
        """
        if not OPENPYXL_AVAILABLE:
            raise ImportError(
                "openpyxl não está instalado. Instale com: pip install openpyxl>=3.1.0"
            )

        wb = Workbook()
        ws = wb.active
        ws.title = "Ata de Escolha"

        header_fill = PatternFill(start_color="ECF0F1", end_color="ECF0F1", fill_type="solid")
        header_font = Font(bold=True, size=10)
        title_font = Font(bold=True, size=12)
        normal_font = Font(size=9)
        center = Alignment(horizontal='center', vertical='center')
        left = Alignment(horizontal='left', vertical='center')
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

        # Título
        row_idx = 1
        ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=13)
        c = ws.cell(row=row_idx, column=1)
        c.value = "ATA DE ESCOLHA"
        c.font = title_font
        c.alignment = center
        row_idx += 1

        # Lei de referência
        ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=13)
        c = ws.cell(row=row_idx, column=1)
        c.value = ""
        c.font = Font(size=10, italic=True)
        c.alignment = center
        row_idx += 1

        # Cabeçalho institucional (opcional)
        if cabecalho:
            ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=13)
            c = ws.cell(row=row_idx, column=1)
            c.value = cabecalho
            c.font = Font(size=10, bold=True)
            c.alignment = left
            row_idx += 1

        # Espaço
        row_idx += 1

        # Percorre cargos e sessões
        headers = ['Class. Geral', 'Class. Def.', 'Class. NNA', 'RF', 'RG', 'CPF', 'Nome', 
                  'Código EOL', 'DRE', 'Tipo Unidade', 'Unidade Escolhida', 'Tipo Vaga', 'Assinatura']

        for cargo in cargos_list or []:
            cargo_nome = cargo.get('cargo_nome', '')
            sessoes = cargo.get('sessoes', []) or []

            for sessao in sessoes:
                numero_sessao = sessao.get('numero_sessao', '')
                horario_formatado = sessao.get('horario_formatado', '')
                sessao_texto = f"{numero_sessao}ª SESSÃO"
                if horario_formatado:
                    sessao_texto += f" - Horário: {horario_formatado}"

                # Linha de sessão
                ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=13)
                c = ws.cell(row=row_idx, column=1)
                c.value = sessao_texto
                c.font = Font(bold=True, size=11)
                c.alignment = left
                c.fill = PatternFill(start_color="34495e", end_color="34495e", fill_type="solid")
                c.font = Font(bold=True, size=11, color="FFFFFF")
                row_idx += 1

                # Linha de cargo
                ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=13)
                c = ws.cell(row=row_idx, column=1)
                c.value = f"CARGO: {cargo_nome}"
                c.font = Font(bold=True, size=11)
                c.alignment = left
                c.fill = PatternFill(start_color="667eea", end_color="667eea", fill_type="solid")
                c.font = Font(bold=True, size=11, color="FFFFFF")
                row_idx += 1

                # Cabeçalho da tabela
                for col, h in enumerate(headers, start=1):
                    cell = ws.cell(row=row_idx, column=col)
                    cell.value = h
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = center if col in (1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 13) else left
                    cell.border = border

                # Dados
                for r, cand in enumerate(sessao.get('candidatos', []), start=row_idx + 1):
                    candidato_obj = cand.get('candidato', {}) if isinstance(cand.get('candidato'), dict) else {}
                    
                    values = [
                        '-' if str(cand.get('classificacao', '-')) == 'None' else str(cand.get('classificacao', '-')),
                        '-' if str(cand.get('classificacao_pcd', '-')) == 'None' else str(cand.get('classificacao_pcd', '-')),
                        '-' if str(cand.get('classificacao_nna', '-')) == 'None' else str(cand.get('classificacao_nna', '-')),
                    ]
                    
                    # RF, RG, CPF
                    # RF = registro_funcional (do model candidato)
                    rf = cand.get('rf', '') or (candidato_obj.get('registro_funcional', '') if isinstance(candidato_obj, dict) else '') or '-'
                    rg = cand.get('rg', '') or (candidato_obj.get('rg', '') if isinstance(candidato_obj, dict) else '') or '-'
                    cpf = cand.get('cpf', '') or (candidato_obj.get('cpf', '') if isinstance(candidato_obj, dict) else '') or '-'
                    values.extend([str(rf), str(rg), str(cpf)])
                    
                    # Nome
                    status_especial = cand.get('status_especial', '')
                    if status_especial:
                        nome = status_especial
                    else:
                        nome = cand.get('nome', '') or (candidato_obj.get('nome', 'N/A') if isinstance(candidato_obj, dict) else 'N/A')
                    values.append(nome)
                    
                    # Dados da escola escolhida
                    values.extend([
                        str(cand.get('codigo_eol', '-') or '-'),
                        str(cand.get('dre_codigo', '-') or '-'),
                        str(cand.get('tipo_unidade', '-') or '-'),
                        str(cand.get('nome_escola_escolhida', '-') or '-'),
                        str(cand.get('tipo_vaga', '-') or '-'),
                        str(cand.get('assinatura', 'Não Escolha') or 'Não Escolha'),
                    ])

                    for col, val in enumerate(values, start=1):
                        cell = ws.cell(row=r, column=col)
                        cell.value = val
                        cell.font = normal_font
                        cell.alignment = center if col in (1, 2, 3, 4, 5, 6, 8, 9, 10, 12, 13) else left
                        cell.border = border

                # Atualiza row_idx após os dados da sessão + linha em branco
                row_idx = row_idx + 1 + len(sessao.get('candidatos', [])) + 1

        # Largura das colunas
        column_widths = {
            'A': 12,  # Class. Geral
            'B': 12,  # Class. Def.
            'C': 12,  # Class. NNA
            'D': 12,  # RF
            'E': 15,  # RG
            'F': 15,  # CPF
            'G': 35,  # Nome
            'H': 12,  # Código EOL
            'I': 10,  # DRE
            'J': 15,  # Tipo Unidade
            'K': 40,  # Unidade Escolhida
            'L': 10,  # Tipo Vaga
            'M': 12,  # Assinatura
        }
        
        for col_letter, width in column_widths.items():
            ws.column_dimensions[col_letter].width = width

        # Salvar em buffer
        from io import BytesIO
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        resp = HttpResponse(
            buf.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        resp['Content-Disposition'] = f'attachment; filename="{filename}"'
        return resp
