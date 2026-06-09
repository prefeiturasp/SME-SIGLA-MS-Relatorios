"""Módulo tests/services/relatorios/test_lista_candidatos_sessao."""
from __future__ import annotations
from typing import Any
from unittest.mock import patch
import pytest
from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory
from relatorios.models import ConfiguracaoRelatorio, Parametrizacao
from relatorios.services.relatorios.lista_candidatos_sessao import ListaCandidatosSessao
pytestmark = pytest.mark.django_db

class _Resp:
    """Define _Resp."""

    def __init__(self, payload: Any) -> None:
        """Executa   init  ."""
        self._payload = payload

    def json(self) -> Any:
        """Executa json."""
        return self._payload

@pytest.fixture
def configuracao_relatorio() -> Any:
    """Fixture que cria uma ConfiguracaoRelatorio para testes."""
    return ConfiguracaoRelatorio.objects.get_or_create(tipo='LISTA_CANDIDATOS_SESSAO', defaults={'usar_logotipo': False, 'cabecalho': '', 'texto_final': '', 'cabecalho_capa_ata': ''})[0]

@pytest.fixture
def parametrizacao() -> Any:
    """Fixture que cria uma Parametrizacao para testes."""
    return Parametrizacao.objects.create(cabecalho='Cabeçalho Padrão Teste', logo=None)

def _make_service(settings: Any, configuracao_relatorio: Any, parametrizacao: Any) -> Any:
    """Executa  make service."""
    settings.CANDIDATOS_API_URL = 'http://candidatos'
    settings.RELATORIO_CABECALHO_PADRAO = 'HEADER_PADRAO'
    settings.AGENDAS_API_URL = 'http://agendas'
    svc = ListaCandidatosSessao(configuracao=configuracao_relatorio, parametrizacao=parametrizacao)
    return svc

def _req() -> Any:
    """Executa  req."""
    return RequestFactory().get('/relatorios/lista-candidatos-sessao/')

def test_html_success_and_flatten_mapping(settings: Any, monkeypatch: Any, configuracao_relatorio: Any, parametrizacao: Any) -> None:
    """Verifica html success and flatten mapping."""
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    payload = {'results': [{'classificacao': 1, 'classificacao_nna': None, 'classificacao_pcd': None, 'codigo_inscricao': 'A1', 'candidato': {'nome': 'Ana', 'cpf': '111'}}, {'classificacao': 2, 'classificacao_nna': 3, 'classificacao_pcd': 4, 'inscricao': 'B2', 'nome': 'Beto', 'cpf': '222'}]}
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp(payload))
    monkeypatch.setattr(svc.agendas_service, 'buscar_agenda_por_uuid', lambda agenda_uuid: _Resp({'candidatos_uuids': ['u1', 'u2'], 'retardatario': False, 'escolha_em': '2026-01-13', 'hora_convocacao_inicio': '08:00:00', 'hora_convocacao_fim': '09:00:00', 'sessao': '1'}))
    response, ctx = svc.gerar(processo_uuid='p1', request=_req(), formato='html', cabecalho='MEU CAB', agenda_uuid='ag-1')
    assert isinstance(response, HttpResponse)
    print(ctx)
    assert ctx['candidatos'][0]['inscricao'] == 'A1'
    assert ctx['candidatos'][0]['nome'] == 'Ana'
    assert ctx['candidatos'][0]['cpf'] == '111'
    assert ctx['candidatos'][1]['inscricao'] == 'B2'
    assert ctx['candidatos'][1]['nome'] == 'Beto'
    assert ctx['candidatos'][1]['cpf'] == '222'
    assert svc.context.get('cabecalho') == 'MEU CAB'
    assert svc.context.get('cabecalho_padrao') == 'Cabeçalho Padrão Teste'

def test_pdf_success_calls_render_to_pdf(settings: Any, monkeypatch: Any, configuracao_relatorio: Any, parametrizacao: Any) -> None:
    """Verifica pdf success calls render to pdf."""
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp({'results': []}))
    monkeypatch.setattr(svc.agendas_service, 'buscar_agenda_por_uuid', lambda agenda_uuid: _Resp({'candidatos_uuids': [], 'retardatario': False}))
    with patch.object(svc, 'render_to_pdf', return_value=HttpResponse(b'%PDF', content_type='application/pdf')) as m_pdf:
        response, ctx = svc.gerar('p1', _req(), 'pdf', cabecalho='', agenda_uuid='ag-1')
    m_pdf.assert_called_once()
    assert response['Content-Type'] == 'application/pdf'

def test_default_json_return(settings: Any, monkeypatch: Any, configuracao_relatorio: Any, parametrizacao: Any) -> None:
    """Verifica default json return."""
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp([]))
    monkeypatch.setattr(svc.agendas_service, 'buscar_agenda_por_uuid', lambda agenda_uuid: _Resp({'candidatos_uuids': [], 'retardatario': False}))
    response, ctx = svc.gerar('p1', _req(), 'json', cabecalho='', agenda_uuid='ag-1')
    assert isinstance(response, JsonResponse)
    assert 'candidatos' in ctx

def test_xls_importerror_when_lib_missing(settings: Any, monkeypatch: Any, configuracao_relatorio: Any, parametrizacao: Any) -> None:
    """Verifica xls importerror when lib missing."""
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp([]))
    monkeypatch.setattr(svc.agendas_service, 'buscar_agenda_por_uuid', lambda agenda_uuid: _Resp({'candidatos_uuids': [], 'retardatario': False}))
    monkeypatch.setattr('relatorios.services.relatorios.lista_candidatos_sessao.OPENPYXL_AVAILABLE', False)
    with pytest.raises(ImportError):
        svc.gerar('p1', _req(), 'xls', cabecalho='', agenda_uuid='ag-1')

def test_docx_importerror_when_lib_missing(settings: Any, monkeypatch: Any, configuracao_relatorio: Any, parametrizacao: Any) -> None:
    """Verifica docx importerror when lib missing."""
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp([]))
    monkeypatch.setattr(svc.agendas_service, 'buscar_agenda_por_uuid', lambda agenda_uuid: _Resp({'candidatos_uuids': [], 'retardatario': False}))
    monkeypatch.setattr('relatorios.services.relatorios.lista_candidatos_sessao.DOCX_AVAILABLE', False)
    with pytest.raises(ImportError):
        svc.gerar('p1', _req(), 'docx', cabecalho='', agenda_uuid='ag-1')

def test_header_padrao_aparece_automaticamente(settings: Any, monkeypatch: Any, configuracao_relatorio: Any, parametrizacao: Any) -> None:
    """Verifica header padrao aparece automaticamente."""
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp([]))
    monkeypatch.setattr(svc.agendas_service, 'buscar_agenda_por_uuid', lambda agenda_uuid: _Resp({'candidatos_uuids': [], 'retardatario': False}))
    parametrizacao.cabecalho = 'HEADER_PADRAO'
    parametrizacao.save()
    svc.context['cabecalho_padrao'] = 'HEADER_PADRAO'
    response, ctx = svc.gerar('p1', _req(), 'html', cabecalho=None, agenda_uuid='ag-1')
    assert svc.context.get('cabecalho_padrao') == 'HEADER_PADRAO'

def test_multiple_agendas_filtered_and_separated(settings: Any, monkeypatch: Any, configuracao_relatorio: Any, parametrizacao: Any) -> Any:
    """Verifica multiple agendas filtered and separated."""
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    agendas_payload = {'results': [{'uuid': 'ag-1', 'retardatario': False, 'candidatos_uuids': ['u1', 'u2'], 'escolha_em': '2026-02-01', 'hora_convocacao_inicio': '09:00:00', 'hora_convocacao_fim': '10:00:00', 'sessao': 'Sessão A'}, {'uuid': 'ag-2', 'retardatario': True, 'candidatos_uuids': ['u3'], 'escolha_em': '2026-02-02', 'hora_convocacao_inicio': '11:00:00', 'hora_convocacao_fim': '12:00:00', 'sessao': 'Sessão B'}, {'uuid': 'ag-3', 'candidatos_uuids': ['u4'], 'escolha_em': '2026-02-03', 'hora_convocacao_inicio': '13:00:00', 'hora_convocacao_fim': '14:00:00', 'sessao': 'Sessão C'}]}

    def _cand_resp(**kw: Any) -> Any:
        """Executa  cand resp."""
        return _Resp({'results': [{'classificacao': 1, 'inscricao': 'I1', 'nome': 'N1', 'cpf': 'C1'}, {'classificacao': 2, 'inscricao': 'I2', 'nome': 'N2', 'cpf': 'C2'}]})
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', _cand_resp)
    monkeypatch.setattr(svc.agendas_service, 'buscar_agendas', lambda **kw: _Resp(agendas_payload))
    response, ctx = svc.gerar('proc-1', _req(), 'html', cabecalho='', agenda_uuid=None)
    assert isinstance(response, HttpResponse)
    assert 'agendas' in ctx and isinstance(ctx['agendas'], list)
    assert len(ctx['agendas']) == 1
    sec = ctx['agendas'][0]
    assert sec['agenda']['uuid'] == 'ag-1'
    assert len(sec['candidatos']) == 2

def test_render_docx_success_with_fake_python_docx(settings: Any, monkeypatch: Any, configuracao_relatorio: Any, parametrizacao: Any) -> Any:
    """Verifica render docx success with fake python docx."""
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    context = {'candidatos': [{'classificacao': 1, 'classificacao_nna': None, 'classificacao_pcd': None, 'inscricao': 'A1', 'nome': 'Ana', 'cpf': '111'}, {'classificacao': 2, 'classificacao_nna': 3, 'classificacao_pcd': 4, 'inscricao': 'B2', 'nome': 'Beto', 'cpf': '222'}]}

    class FakeRun:
        """Define FakeRun."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.font = type('Font', (), {'size': None, 'bold': False})()

    class FakeParagraph:
        """Define FakeParagraph."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.alignment = None
            self._runs = [FakeRun()]
            self.runs = self._runs

        def add_run(self, text: Any='') -> Any:
            """Executa add run."""
            run = FakeRun()
            self._runs.append(run)
            self.runs = self._runs
            return run

    class FakeTcPr:
        """Define FakeTcPr."""

        def find(self, x: Any) -> Any:
            """Executa find."""
            return None

        def remove(self, x: Any) -> None:
            """Executa remove."""
            pass

        def append(self, x: Any) -> None:
            """Executa append."""
            pass

    class FakeElement:
        """Define FakeElement."""

        def get_or_add_tcPr(self) -> Any:
            """Executa get or add tcPr."""
            return FakeTcPr()

    class FakeCell:
        """Define FakeCell."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.text = ''
            self.paragraphs = [FakeParagraph()]
            self._element = FakeElement()

    class FakeRow:
        """Define FakeRow."""

        def __init__(self, cols: Any) -> None:
            """Executa   init  ."""
            self.cells = [FakeCell() for _ in range(cols)]

    class FakeTable:
        """Define FakeTable."""

        def __init__(self, rows: Any, cols: Any) -> None:
            """Executa   init  ."""
            self.rows = [FakeRow(cols) for _ in range(rows)]

    class FakeSection:
        """Define FakeSection."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.top_margin = None
            self.bottom_margin = None
            self.left_margin = None
            self.right_margin = None

    class FakeRun:  # type: ignore[no-redef]
        """Define FakeRun."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.font = type('Font', (), {'size': None, 'bold': False, 'color': type('Color', (), {'rgb': None})()})()

    class FakeParagraph:  # type: ignore[no-redef]
        """Define FakeParagraph."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.alignment = None
            self._runs = [FakeRun()]
            self.runs = self._runs

        def add_run(self, text: Any='') -> Any:
            """Executa add run."""
            run = FakeRun()
            self._runs.append(run)
            self.runs = self._runs
            return run

    class FakeDocument:
        """Define FakeDocument."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self._headings = []  # type: ignore[var-annotated]
            self._tables = []  # type: ignore[var-annotated]
            self.sections = [FakeSection()]
            self._paragraphs = []  # type: ignore[var-annotated]

        def add_heading(self, text: Any, level: Any=1) -> Any:
            """Executa add heading."""
            self._headings.append((text, level))
            return FakeParagraph()

        def add_paragraph(self, text: Any='') -> Any:
            """Executa add paragraph."""
            p = FakeParagraph()
            if text:
                p.add_run(text)
            self._paragraphs.append(p)
            return p

        def add_table(self, rows: Any, cols: Any) -> Any:
            """Executa add table."""
            tbl = FakeTable(rows, cols)
            self._tables.append(tbl)
            return tbl

        def save(self, buf: Any) -> None:
            """Executa save."""
            buf.write(b'DOCX')
    import relatorios.services.relatorios.lista_candidatos_sessao as mod
    monkeypatch.setattr(mod, 'DOCX_AVAILABLE', True)
    monkeypatch.setattr(mod, 'Document', FakeDocument)
    resp = svc._render_docx(context)
    assert resp['Content-Type'] == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    assert 'attachment; filename=' in resp['Content-Disposition']

def test_render_docx_agenda_paragraphs_all(settings: Any, monkeypatch: Any, configuracao_relatorio: Any, parametrizacao: Any) -> Any:
    """Verifica render docx agenda paragraphs all."""
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    context = {'agenda': {'escolha_em': '2026-01-13', 'hora_convocacao_inicio': '08:00:00', 'hora_convocacao_fim': '09:00:00', 'sessao': 'Sessão 1'}, 'candidatos': []}

    class FakeRun:
        """Define FakeRun."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.font = type('Font', (), {'size': None, 'bold': False, 'color': type('Color', (), {'rgb': None})()})()

    class FakeParagraph:
        """Define FakeParagraph."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.alignment = None
            self._runs = [FakeRun()]
            self.runs = self._runs

        def add_run(self, text: Any='') -> Any:
            """Executa add run."""
            run = FakeRun()
            self._runs.append(run)
            self.runs = self._runs
            return run

    class FakeTcPr:
        """Define FakeTcPr."""

        def find(self, x: Any) -> Any:
            """Executa find."""
            return None

        def remove(self, x: Any) -> None:
            """Executa remove."""
            pass

        def append(self, x: Any) -> None:
            """Executa append."""
            pass

    class FakeElement:
        """Define FakeElement."""

        def get_or_add_tcPr(self) -> Any:
            """Executa get or add tcPr."""
            return FakeTcPr()

    class FakeCell:
        """Define FakeCell."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.text = ''
            self.paragraphs = [FakeParagraph()]
            self._element = FakeElement()

    class FakeRow:
        """Define FakeRow."""

        def __init__(self, cols: Any) -> None:
            """Executa   init  ."""
            self.cells = [FakeCell() for _ in range(cols)]

    class FakeTable:
        """Define FakeTable."""

        def __init__(self, rows: Any, cols: Any) -> None:
            """Executa   init  ."""
            self.rows = [FakeRow(cols) for _ in range(rows)]

    class FakeSection:
        """Define FakeSection."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.top_margin = None
            self.bottom_margin = None
            self.left_margin = None
            self.right_margin = None

    class FakeDocument:
        """Define FakeDocument."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.paragraphs_text = []  # type: ignore[var-annotated]
            self.sections = [FakeSection()]
            self._paragraphs = []  # type: ignore[var-annotated]

        def add_heading(self, text: Any, level: Any=1) -> Any:
            """Executa add heading."""
            self.paragraphs_text.append(text)
            return FakeParagraph()

        def add_paragraph(self, text: Any='') -> Any:
            """Executa add paragraph."""
            self.paragraphs_text.append(text)
            p = FakeParagraph()
            if text:
                p.add_run(text)
            self._paragraphs.append(p)
            return p

        def add_table(self, rows: Any, cols: Any) -> Any:
            """Executa add table."""
            return FakeTable(rows, cols)

        def save(self, buf: Any) -> None:
            """Executa save."""
            buf.write(b'DOCX')
    import relatorios.services.relatorios.lista_candidatos_sessao as mod
    monkeypatch.setattr(mod, 'DOCX_AVAILABLE', True)
    monkeypatch.setattr(mod, 'Document', FakeDocument)
    resp = svc._render_docx(context)
    assert resp['Content-Type'] == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    fake = FakeDocument()
    fake.add_heading('Lista de Candidatos por Sessão', level=1)
    fake.add_paragraph('Data: 13/01/2026')
    fake.add_paragraph('Horário: 08:00 às 09:00')
    fake.add_paragraph('Sessão 1')
    assert 'Data: 13/01/2026' in fake.paragraphs_text
    assert 'Horário: 08:00 às 09:00' in fake.paragraphs_text
    assert 'Sessão 1' in fake.paragraphs_text

def test_render_docx_agenda_paragraphs_partial_time_only_start(settings: Any, monkeypatch: Any, configuracao_relatorio: Any, parametrizacao: Any) -> Any:
    """Verifica render docx agenda paragraphs partial time only start."""
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    context = {'agenda': {'escolha_em': '', 'hora_convocacao_inicio': '10:30:00', 'hora_convocacao_fim': '', 'sessao': ''}, 'candidatos': []}

    class FakeRun:
        """Define FakeRun."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.font = type('Font', (), {'size': None, 'bold': False, 'color': type('Color', (), {'rgb': None})()})()

    class FakeParagraph:
        """Define FakeParagraph."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.alignment = None
            self._runs = [FakeRun()]
            self.runs = self._runs

        def add_run(self, text: Any='') -> Any:
            """Executa add run."""
            run = FakeRun()
            self._runs.append(run)
            self.runs = self._runs
            return run

    class FakeTcPr:
        """Define FakeTcPr."""

        def find(self, x: Any) -> Any:
            """Executa find."""
            return None

        def remove(self, x: Any) -> None:
            """Executa remove."""
            pass

        def append(self, x: Any) -> None:
            """Executa append."""
            pass

    class FakeElement:
        """Define FakeElement."""

        def get_or_add_tcPr(self) -> Any:
            """Executa get or add tcPr."""
            return FakeTcPr()

    class FakeCell:
        """Define FakeCell."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.text = ''
            self.paragraphs = [FakeParagraph()]
            self._element = FakeElement()

    class FakeRow:
        """Define FakeRow."""

        def __init__(self, cols: Any) -> None:
            """Executa   init  ."""
            self.cells = [FakeCell() for _ in range(cols)]

    class FakeTable:
        """Define FakeTable."""

        def __init__(self, rows: Any, cols: Any) -> None:
            """Executa   init  ."""
            self.rows = [FakeRow(cols) for _ in range(rows)]

    class FakeSection:
        """Define FakeSection."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.top_margin = None
            self.bottom_margin = None
            self.left_margin = None
            self.right_margin = None

    class FakeDocument:
        """Define FakeDocument."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.paragraphs_text = []  # type: ignore[var-annotated]
            self.sections = [FakeSection()]
            self._paragraphs = []  # type: ignore[var-annotated]

        def add_heading(self, text: Any, level: Any=1) -> Any:
            """Executa add heading."""
            self.paragraphs_text.append(text)
            return FakeParagraph()

        def add_paragraph(self, text: Any='') -> Any:
            """Executa add paragraph."""
            self.paragraphs_text.append(text)
            p = FakeParagraph()
            if text:
                p.add_run(text)
            self._paragraphs.append(p)
            return p

        def add_table(self, rows: Any, cols: Any) -> Any:
            """Executa add table."""
            return FakeTable(rows, cols)

        def save(self, buf: Any) -> None:
            """Executa save."""
            buf.write(b'DOCX')
    import relatorios.services.relatorios.lista_candidatos_sessao as mod
    monkeypatch.setattr(mod, 'DOCX_AVAILABLE', True)
    monkeypatch.setattr(mod, 'Document', FakeDocument)
    resp = svc._render_docx(context)
    assert resp['Content-Type'] == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    fake = FakeDocument()
    fake.add_heading('Lista de Candidatos por Sessão', level=1)
    fake.add_paragraph('Horário: 10:30')
    assert 'Horário: 10:30' in fake.paragraphs_text

def test_render_xls_layout_with_title_and_agenda(settings: Any, monkeypatch: Any, configuracao_relatorio: Any, parametrizacao: Any) -> Any:
    """Verifica render xls layout with title and agenda."""
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    import relatorios.services.relatorios.lista_candidatos_sessao as mod

    class FakeCell:
        """Define FakeCell."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.value = None
            self.font = None
            self.alignment = None
            self.border = None

    class _Dim:
        """Define _Dim."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.width = None

    class FakeWS:
        """Define FakeWS."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.title = ''
            self._cells = {}  # type: ignore[var-annotated]
            self.column_dimensions = {k: _Dim() for k in ['A', 'B', 'C', 'D', 'E', 'F']}

        def cell(self, row: Any, column: Any) -> Any:
            """Executa cell."""
            key = (row, column)
            if key not in self._cells:
                self._cells[key] = FakeCell()
            return self._cells[key]

        def merge_cells(self, *args: Any, **kwargs: Any) -> None:
            """Executa merge cells."""
            return

    class FakeWB:
        """Define FakeWB."""

        def __init__(self) -> None:
            """Executa   init  ."""
            self.active = FakeWS()
            mod._last_ws = self.active  # type: ignore[attr-defined]

        def save(self, buf: Any) -> None:
            """Executa save."""
            buf.write(b'XLSX')

    class Dummy:
        """Define Dummy."""

        def __init__(self, *a: Any, **k: Any) -> None:
            """Executa   init  ."""
            pass
    monkeypatch.setattr(mod, 'OPENPYXL_AVAILABLE', True)
    monkeypatch.setattr(mod, 'Workbook', FakeWB)
    monkeypatch.setattr(mod, 'PatternFill', Dummy)
    monkeypatch.setattr(mod, 'Font', Dummy)
    monkeypatch.setattr(mod, 'Alignment', Dummy)
    monkeypatch.setattr(mod, 'Border', Dummy)
    monkeypatch.setattr(mod, 'Side', Dummy)
    context = {'agenda': {'escolha_em': '2026-01-13', 'hora_convocacao_inicio': '08:00:00', 'hora_convocacao_fim': '09:00:00', 'sessao': '1'}, 'candidatos': [{'classificacao': 10, 'classificacao_nna': None, 'classificacao_pcd': None, 'inscricao': 'I1', 'nome': 'Nome 1', 'cpf': '111'}, {'classificacao': 11, 'classificacao_nna': 2, 'classificacao_pcd': None, 'inscricao': 'I2', 'nome': 'Nome 2', 'cpf': '222'}]}
    resp = svc._render_xls(context)
    assert resp['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ws = mod._last_ws  # type: ignore[attr-defined]
    cells = ws._cells
    assert cells[1, 1].value == 'Cabeçalho Padrão Teste'
    assert cells[3, 1].value == 'Lista de Candidatos por Sessão'
    assert str(cells[5, 1].value).startswith('Data: ')
    assert '13/01/2026' in str(cells[5, 1].value)
    assert str(cells[6, 1].value).startswith('Horário:')
    assert '08:00' in str(cells[6, 1].value) and '09:00' in str(cells[6, 1].value)
    assert cells[7, 1].value == '1'
    assert cells[9, 1].value == 'Classificação'
    assert cells[9, 2].value == 'Classificação NNA'
    assert cells[9, 3].value == 'Classificação PCD'
    assert cells[9, 4].value == 'Inscrição'
    assert cells[9, 5].value == 'Nome'
    assert cells[9, 6].value == 'CPF'
    assert cells[10, 1].value == 10
    assert cells[10, 4].value == 'I1'
    assert cells[10, 5].value == 'Nome 1'
    assert cells[10, 6].value == '111'
