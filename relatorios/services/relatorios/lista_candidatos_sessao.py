import logging
from typing import List, Dict, Any, Tuple
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.conf import settings

from relatorios.services.base.relatorio_base import RelatorioBase
from relatorios.services.candidatos_api_service import CandidatosService
from relatorios.services.agendas_api_service import AgendasService

logger = logging.getLogger(__name__)

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    OPENPYXL_AVAILABLE = True
except Exception:
    OPENPYXL_AVAILABLE = False

try:
    from docx import Document
    from docx.shared import Pt
    DOCX_AVAILABLE = True
except Exception:
    DOCX_AVAILABLE = False


class ListaCandidatosSessao(RelatorioBase):
    """
    Gera relatório de lista de candidatos por sessão, a partir de uma lista de UUIDs.
    Suporta HTML, PDF, XLS e DOCX.
    """

    TEMPLATE_NAME = 'relatorios/lista_candidatos_sessao.html'

    def __init__(self):
        self.candidatos_service = CandidatosService(base_url=settings.CANDIDATOS_API_URL)
        self.agendas_service = AgendasService(base_url=settings.AGENDAS_API_URL)

    def _fetch_candidatos(self, candidatos_uuids: List[str], order_by: str = 'ranking_escolha') -> List[Dict[str, Any]]:
        if not candidatos_uuids:
            return []
        resp = self.candidatos_service.buscar_por_uuids(uuids=candidatos_uuids, order_by=order_by)
        data = resp.json()
        if isinstance(data, dict) and 'results' in data:
            return data.get('results', [])
        if isinstance(data, list):
            return data
        return []

    @staticmethod
    def _flatten_candidato(item: Dict[str, Any]) -> Dict[str, Any]:
        cand = item.get('candidato') or {}
        return {
            'classificacao': item.get('classificacao'),
            'classificacao_nna': item.get('classificacao_nna'),
            'classificacao_pcd': item.get('classificacao_pcd'),
            'inscricao': item.get('codigo_inscricao') or item.get('inscricao'),
            'nome': cand.get('nome') or item.get('nome'),
            'cpf': cand.get('cpf') or item.get('cpf'),
        }

    def _build_context(self, candidatos: List[Dict[str, Any]], agenda_data: Dict[str, Any]) -> Dict[str, Any]:
        linhas = [self._flatten_candidato(c) for c in candidatos]
        return {'candidatos': linhas, 'agenda': agenda_data}

    def _render_xls(self, context: Dict[str, Any], filename: str = 'lista_candidatos_sessao.xlsx') -> HttpResponse:
        if not OPENPYXL_AVAILABLE:
            raise ImportError("openpyxl não está instalado. Instale com: pip install openpyxl>=3.1.0")

        wb = Workbook()
        ws = wb.active
        ws.title = "Candidatos"

        header_fill = PatternFill(start_color="ECF0F1", end_color="ECF0F1", fill_type="solid")
        header_font = Font(bold=True, size=11)
        normal_font = Font(size=10)
        center = Alignment(horizontal='center', vertical='center')
        left = Alignment(horizontal='left', vertical='center')
        border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

        # Título e informações da agenda acima da tabela
        row_idx = 1
        ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=6)
        title_cell = ws.cell(row=row_idx, column=1)
        title_cell.value = "Lista de Candidatos por Sessão"
        title_cell.font = Font(bold=True, size=14)
        title_cell.alignment = center
        row_idx += 2  # linha em branco após o título
        agenda = context.get('agenda') or {}
        escolha_em = agenda.get('escolha_em') or ''
        hora_ini = agenda.get('hora_convocacao_inicio') or ''
        hora_fim = agenda.get('hora_convocacao_fim') or ''
        sessao = agenda.get('sessao') or ''
        def _fmt_data(date_str: str) -> str:
            return f"{date_str[8:10]}/{date_str[5:7]}/{date_str[:4]}" if len(date_str) >= 10 else date_str
        def _fmt_hora(time_str: str) -> str:
            return time_str[:5] if len(time_str) >= 5 else time_str
        if escolha_em:
            ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=6)
            c = ws.cell(row=row_idx, column=1)
            c.value = f"Data: {_fmt_data(escolha_em)}"
            c.font = Font(bold=True, size=12)
            c.alignment = left
            row_idx += 1
        if hora_ini or hora_fim:
            ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=6)
            c = ws.cell(row=row_idx, column=1)
            ini = _fmt_hora(hora_ini) if hora_ini else ''
            fim = _fmt_hora(hora_fim) if hora_fim else ''
            c.value = f"Horário: {ini} às {fim}" if ini and fim else f"Horário: {ini or fim}"
            c.font = Font(bold=True, size=12)
            c.alignment = left
            row_idx += 1
        if sessao:
            ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=6)
            c = ws.cell(row=row_idx, column=1)
            c.value = str(sessao)
            c.font = Font(bold=True, size=12)
            c.alignment = left
            row_idx += 1
        if row_idx > 1:
            row_idx += 1

        headers = ['Classificação', 'Classificação NNA', 'Classificação PCD', 'Inscrição', 'Nome', 'CPF']
        for col, h in enumerate(headers, start=1):
            cell = ws.cell(row=row_idx, column=col)
            cell.value = h
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center
            cell.border = border

        for i, row in enumerate(context.get('candidatos', []), start=row_idx + 1):
            values = [
                row.get('classificacao'),
                row.get('classificacao_nna'),
                row.get('classificacao_pcd'),
                row.get('inscricao'),
                row.get('nome'),
                row.get('cpf'),
            ]
            for col, val in enumerate(values, start=1):
                cell = ws.cell(row=i, column=col)
                cell.value = val
                cell.font = normal_font
                cell.alignment = center if col in (1, 2, 3) else left
                cell.border = border

        ws.column_dimensions['A'].width = 16
        ws.column_dimensions['B'].width = 22
        ws.column_dimensions['C'].width = 22
        ws.column_dimensions['D'].width = 16
        ws.column_dimensions['E'].width = 40
        ws.column_dimensions['F'].width = 20

        import io
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        resp = HttpResponse(
            buf.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        resp['Content-Disposition'] = f'attachment; filename="{filename}"'
        return resp

    def _render_docx(self, context: Dict[str, Any], filename: str = 'lista_candidatos_sessao.docx') -> HttpResponse:
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx não está instalado. Instale com: pip install python-docx>=0.8.11")

        doc = Document()
        doc.add_heading('Lista de Candidatos por Sessão', level=1)
        # Informações da agenda no topo
        agenda = context.get('agenda') or {}
        escolha_em = agenda.get('escolha_em') or ''
        hora_ini = agenda.get('hora_convocacao_inicio') or ''
        hora_fim = agenda.get('hora_convocacao_fim') or ''
        sessao = agenda.get('sessao') or ''
        def _fmt_data(date_str: str) -> str:
            return f"{date_str[8:10]}/{date_str[5:7]}/{date_str[:4]}" if len(date_str) >= 10 else date_str
        def _fmt_hora(time_str: str) -> str:
            return time_str[:5] if len(time_str) >= 5 else time_str
        if escolha_em:
            doc.add_paragraph(f"Data: {_fmt_data(escolha_em)}")
        if hora_ini or hora_fim:
            ini = _fmt_hora(hora_ini) if hora_ini else ''
            fim = _fmt_hora(hora_fim) if hora_fim else ''
            doc.add_paragraph(f"Horário: {ini} às {fim}" if ini and fim else f"Horário: {ini or fim}")
        if sessao:
            doc.add_paragraph(str(sessao))
        rows = len(context.get('candidatos', [])) + 1
        table = doc.add_table(rows=rows, cols=6)
        hdr_cells = table.rows[0].cells
        headers = ['Classificação', 'Classificação NNA', 'Classificação PCD', 'Inscrição', 'Nome', 'CPF']
        for idx, h in enumerate(headers):
            hdr_cells[idx].text = h
        for i, row in enumerate(context.get('candidatos', []), start=1):
            cells = table.rows[i].cells
            cells[0].text = str(row.get('classificacao') or '')
            cells[1].text = str(row.get('classificacao_nna') or '')
            cells[2].text = str(row.get('classificacao_pcd') or '')
            cells[3].text = str(row.get('inscricao') or '')
            cells[4].text = str(row.get('nome') or '')
            cells[5].text = str(row.get('cpf') or '')

        import io
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        resp = HttpResponse(
            buf.read(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        resp['Content-Disposition'] = f'attachment; filename="{filename}"'
        return resp

    def gerar(self, processo_uuid: str, request, formato: str = 'html', cabecalho: str = '', agenda_uuid: str = None, **kwargs) -> Tuple[HttpResponse, Dict[str, Any]]:
        """
        Gera a lista de candidatos por sessão a partir de UUIDs.
        """
        try:
            # Buscar detalhes da agenda para extrair os candidatos_uuids
            agenda_resp = self.agendas_service.buscar_agenda_por_uuid(str(agenda_uuid) if agenda_uuid else '')
            agenda_data = agenda_resp.json()
            candidatos_uuids = []
            if isinstance(agenda_data, dict):
                candidatos_uuids = agenda_data.get('candidatos_uuids') or []
            # Buscar candidatos pelos UUIDs obtidos da agenda
            candidatos = self._fetch_candidatos(candidatos_uuids)
            context = self._build_context(candidatos, agenda_data)
            # Cabeçalho compatível com demais relatórios
            cabecalho_input = (cabecalho or '').strip()
            cabecalho_final = cabecalho_input if cabecalho_input else settings.RELATORIO_CABECALHO_PADRAO
            cabecalho_padrao = settings.RELATORIO_CABECALHO_PADRAO
            context.update({
                'cabecalho': cabecalho_final,
                'cabecalho_padrao': cabecalho_padrao,
            })
        except Exception as exc:
            logger.error('Erro ao processar agenda/candidatos: %s', exc, exc_info=True)
            raise

        if formato == 'pdf':
            logger.info('Gerando PDF lista_candidatos_sessao')
            return self.render_to_pdf(self.TEMPLATE_NAME, context, filename='lista_candidatos_sessao.pdf'), context
        if formato == 'html':
            logger.info('Gerando HTML lista_candidatos_sessao')
            return render(request, self.TEMPLATE_NAME, context), context
        if formato in ('xls', 'xlsx'):
            logger.info('Gerando XLS lista_candidatos_sessao')
            return self._render_xls(context), context
        if formato in ('doc', 'docx'):
            logger.info('Gerando DOCX lista_candidatos_sessao')
            return self._render_docx(context), context

        # padrão: JSON (útil para depuração)
        return JsonResponse(context, safe=False), context


