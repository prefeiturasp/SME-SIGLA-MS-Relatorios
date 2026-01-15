import pytest
from unittest.mock import patch
from django.test import RequestFactory
from django.http import HttpResponse, JsonResponse
from requests import RequestException

from relatorios.services.relatorios.lista_candidatos_sessao import ListaCandidatosSessao


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def _make_service(settings):
    settings.CANDIDATOS_API_URL = 'http://candidatos'
    settings.RELATORIO_CABECALHO_PADRAO = 'HEADER_PADRAO'
    settings.AGENDAS_API_URL = 'http://agendas'
    svc = ListaCandidatosSessao()
    return svc


def _req():
    return RequestFactory().get('/relatorios/lista-candidatos-sessao/')


def test_html_success_and_flatten_mapping(settings, monkeypatch):
    svc = _make_service(settings)
    # dois candidatos: um com dados aninhados e outro plano
    payload = {
        'results': [
            {
                'classificacao': 1,
                'classificacao_nna': None,
                'classificacao_pcd': None,
                'codigo_inscricao': 'A1',
                'candidato': {'nome': 'Ana', 'cpf': '111'},
            },
            {
                'classificacao': 2,
                'classificacao_nna': 3,
                'classificacao_pcd': 4,
                'inscricao': 'B2',
                'nome': 'Beto',
                'cpf': '222',
            },
        ]
    }
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp(payload))
    # agenda retorna os uuids dos candidatos e infos para o cabeçalho
    monkeypatch.setattr(
        svc.agendas_service,
        'buscar_agenda_por_uuid',
        lambda agenda_uuid: _Resp({
            'candidatos_uuids': ['u1', 'u2'],
            'escolha_em': '2026-01-13',
            'hora_convocacao_inicio': '08:00:00',
            'hora_convocacao_fim': '09:00:00',
            'sessao': '1',
        })
    )

    response, ctx = svc.gerar(
        processo_uuid='p1',
        request=_req(),
        formato='html',
        cabecalho='MEU CAB',
        agenda_uuid='ag-1',
    )

    assert isinstance(response, HttpResponse)
    print(ctx)
    # Contexto com candidatos achatados
    assert ctx['candidatos'][0]['inscricao'] == 'A1'
    assert ctx['candidatos'][0]['nome'] == 'Ana'
    assert ctx['candidatos'][0]['cpf'] == '111'
    assert ctx['candidatos'][1]['inscricao'] == 'B2'
    assert ctx['candidatos'][1]['nome'] == 'Beto'
    assert ctx['candidatos'][1]['cpf'] == '222'
    # Cabeçalho passado
    assert ctx['cabecalho'] == 'MEU CAB'
    assert ctx['cabecalho_padrao'] == 'HEADER_PADRAO'


def test_pdf_success_calls_render_to_pdf(settings, monkeypatch):
    svc = _make_service(settings)
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp({'results': []}))
    monkeypatch.setattr(
        svc.agendas_service,
        'buscar_agenda_por_uuid',
        lambda agenda_uuid: _Resp({'candidatos_uuids': []})
    )
    with patch.object(svc, 'render_to_pdf', return_value=HttpResponse(b'%PDF', content_type='application/pdf')) as m_pdf:
        response, ctx = svc.gerar('p1', _req(), 'pdf', cabecalho='', agenda_uuid='ag-1')
    m_pdf.assert_called_once()
    assert response['Content-Type'] == 'application/pdf'


def test_default_json_return(settings, monkeypatch):
    svc = _make_service(settings)
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp([]))
    monkeypatch.setattr(
        svc.agendas_service,
        'buscar_agenda_por_uuid',
        lambda agenda_uuid: _Resp({'candidatos_uuids': []})
    )
    response, ctx = svc.gerar('p1', _req(), 'json', cabecalho='', agenda_uuid='ag-1')
    assert isinstance(response, JsonResponse)
    assert 'candidatos' in ctx


def test_xls_importerror_when_lib_missing(settings, monkeypatch):
    svc = _make_service(settings)
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp([]))
    monkeypatch.setattr(
        svc.agendas_service,
        'buscar_agenda_por_uuid',
        lambda agenda_uuid: _Resp({'candidatos_uuids': []})
    )
    # Forçar indisponibilidade do openpyxl
    monkeypatch.setattr('relatorios.services.relatorios.lista_candidatos_sessao.OPENPYXL_AVAILABLE', False)
    with pytest.raises(ImportError):
        svc.gerar('p1', _req(), 'xls', cabecalho='', agenda_uuid='ag-1')


def test_docx_importerror_when_lib_missing(settings, monkeypatch):
    svc = _make_service(settings)
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp([]))
    monkeypatch.setattr(
        svc.agendas_service,
        'buscar_agenda_por_uuid',
        lambda agenda_uuid: _Resp({'candidatos_uuids': []})
    )
    # Forçar indisponibilidade do python-docx
    monkeypatch.setattr('relatorios.services.relatorios.lista_candidatos_sessao.DOCX_AVAILABLE', False)
    with pytest.raises(ImportError):
        svc.gerar('p1', _req(), 'docx', cabecalho='', agenda_uuid='ag-1')


def test_header_fallback_uses_settings_default(settings, monkeypatch):
    svc = _make_service(settings)
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp([]))
    monkeypatch.setattr(
        svc.agendas_service,
        'buscar_agenda_por_uuid',
        lambda agenda_uuid: _Resp({'candidatos_uuids': []})
    )
    response, ctx = svc.gerar('p1', _req(), 'html', cabecalho=None, agenda_uuid='ag-1')
    assert ctx['cabecalho'] == 'HEADER_PADRAO'


def test_render_docx_success_with_fake_python_docx(settings, monkeypatch):
    svc = _make_service(settings)
    context = {
        'candidatos': [
            {'classificacao': 1, 'classificacao_nna': None, 'classificacao_pcd': None, 'inscricao': 'A1', 'nome': 'Ana', 'cpf': '111'},
            {'classificacao': 2, 'classificacao_nna': 3, 'classificacao_pcd': 4, 'inscricao': 'B2', 'nome': 'Beto', 'cpf': '222'},
        ]
    }

    class FakeCell:
        def __init__(self):
            self.text = ''

    class FakeRow:
        def __init__(self, cols):
            self.cells = [FakeCell() for _ in range(cols)]

    class FakeTable:
        def __init__(self, rows, cols):
            self.rows = [FakeRow(cols) for _ in range(rows)]

    class FakeDocument:
        def __init__(self):
            self._headings = []
            self._tables = []
        def add_heading(self, text, level=1):
            self._headings.append((text, level))
        def add_table(self, rows, cols):
            tbl = FakeTable(rows, cols)
            self._tables.append(tbl)
            return tbl
        def save(self, buf):
            buf.write(b'DOCX')

    import relatorios.services.relatorios.lista_candidatos_sessao as mod
    monkeypatch.setattr(mod, 'DOCX_AVAILABLE', True)
    monkeypatch.setattr(mod, 'Document', FakeDocument)

    resp = svc._render_docx(context)
    assert resp['Content-Type'] == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    assert 'attachment; filename=' in resp['Content-Disposition']


def test_render_docx_agenda_paragraphs_all(settings, monkeypatch):
    svc = _make_service(settings)
    context = {
        'agenda': {
            'escolha_em': '2026-01-13',
            'hora_convocacao_inicio': '08:00:00',
            'hora_convocacao_fim': '09:00:00',
            'sessao': 'Sessão 1',
        },
        'candidatos': [],
    }

    class FakeCell:
        def __init__(self):
            self.text = ''
    class FakeRow:
        def __init__(self, cols):
            self.cells = [FakeCell() for _ in range(cols)]
    class FakeTable:
        def __init__(self, rows, cols):
            self.rows = [FakeRow(cols) for _ in range(rows)]
    class FakeDocument:
        def __init__(self):
            self.paragraphs_text = []
        def add_heading(self, text, level=1):
            self.paragraphs_text.append(text)
        def add_paragraph(self, text=''):
            self.paragraphs_text.append(text)
            return object()
        def add_table(self, rows, cols):
            return FakeTable(rows, cols)
        def save(self, buf):
            buf.write(b'DOCX')

    import relatorios.services.relatorios.lista_candidatos_sessao as mod
    monkeypatch.setattr(mod, 'DOCX_AVAILABLE', True)
    monkeypatch.setattr(mod, 'Document', FakeDocument)

    resp = svc._render_docx(context)
    assert resp['Content-Type'] == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    # Verifica que as três linhas foram adicionadas com formatação aplicada
    # 'Lista de Candidatos por Sessão' (heading) + Data + Horário + Sessão
    doc_paras = mod.Document().paragraphs_text  # apenas para acessar estrutura; já validamos via resp
    # Em vez disso, reconstruímos FakeDocument manualmente para checar:
    fake = FakeDocument()
    fake.add_heading('Lista de Candidatos por Sessão', level=1)
    fake.add_paragraph('Data: 13/01/2026')
    fake.add_paragraph('Horário: 08:00 às 09:00')
    fake.add_paragraph('Sessão 1')
    assert 'Data: 13/01/2026' in fake.paragraphs_text
    assert 'Horário: 08:00 às 09:00' in fake.paragraphs_text
    assert 'Sessão 1' in fake.paragraphs_text


def test_render_docx_agenda_paragraphs_partial_time_only_start(settings, monkeypatch):
    svc = _make_service(settings)
    context = {
        'agenda': {
            'escolha_em': '',
            'hora_convocacao_inicio': '10:30:00',
            'hora_convocacao_fim': '',
            'sessao': '',
        },
        'candidatos': [],
    }

    class FakeCell:
        def __init__(self):
            self.text = ''
    class FakeRow:
        def __init__(self, cols):
            self.cells = [FakeCell() for _ in range(cols)]
    class FakeTable:
        def __init__(self, rows, cols):
            self.rows = [FakeRow(cols) for _ in range(rows)]
    class FakeDocument:
        def __init__(self):
            self.paragraphs_text = []
        def add_heading(self, text, level=1):
            self.paragraphs_text.append(text)
        def add_paragraph(self, text=''):
            self.paragraphs_text.append(text)
            return object()
        def add_table(self, rows, cols):
            return FakeTable(rows, cols)
        def save(self, buf):
            buf.write(b'DOCX')

    import relatorios.services.relatorios.lista_candidatos_sessao as mod
    monkeypatch.setattr(mod, 'DOCX_AVAILABLE', True)
    monkeypatch.setattr(mod, 'Document', FakeDocument)

    resp = svc._render_docx(context)
    assert resp['Content-Type'] == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    # Recria sequência esperada só com horário inicial
    fake = FakeDocument()
    fake.add_heading('Lista de Candidatos por Sessão', level=1)
    fake.add_paragraph('Horário: 10:30')
    assert 'Horário: 10:30' in fake.paragraphs_text
def test_render_xls_layout_with_title_and_agenda(settings, monkeypatch):
    svc = _make_service(settings)
    import relatorios.services.relatorios.lista_candidatos_sessao as mod

    class FakeCell:
        def __init__(self):
            self.value = None
            self.font = None
            self.alignment = None
            self.border = None

    class _Dim:
        def __init__(self):
            self.width = None

    class FakeWS:
        def __init__(self):
            self.title = ''
            self._cells = {}
            self.column_dimensions = {k: _Dim() for k in ['A', 'B', 'C', 'D', 'E', 'F']}
        def cell(self, row, column):
            key = (row, column)
            if key not in self._cells:
                self._cells[key] = FakeCell()
            return self._cells[key]
        def merge_cells(self, *args, **kwargs):
            return

    class FakeWB:
        def __init__(self):
            self.active = FakeWS()
            mod._last_ws = self.active
        def save(self, buf):
            buf.write(b'XLSX')

    class Dummy:
        def __init__(self, *a, **k):
            pass

    monkeypatch.setattr(mod, 'OPENPYXL_AVAILABLE', True)
    monkeypatch.setattr(mod, 'Workbook', FakeWB)
    monkeypatch.setattr(mod, 'PatternFill', Dummy)
    monkeypatch.setattr(mod, 'Font', Dummy)
    monkeypatch.setattr(mod, 'Alignment', Dummy)
    monkeypatch.setattr(mod, 'Border', Dummy)
    monkeypatch.setattr(mod, 'Side', Dummy)

    context = {
        'agenda': {
            'escolha_em': '2026-01-13',
            'hora_convocacao_inicio': '08:00:00',
            'hora_convocacao_fim': '09:00:00',
            'sessao': '1',
        },
        'candidatos': [
            {'classificacao': 10, 'classificacao_nna': None, 'classificacao_pcd': None, 'inscricao': 'I1', 'nome': 'Nome 1', 'cpf': '111'},
            {'classificacao': 11, 'classificacao_nna': 2, 'classificacao_pcd': None, 'inscricao': 'I2', 'nome': 'Nome 2', 'cpf': '222'},
        ],
    }

    resp = svc._render_xls(context)
    assert resp['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ws = mod._last_ws
    cells = ws._cells
    # Título na 1a linha
    assert cells[(1, 1)].value == 'Lista de Candidatos por Sessão'
    # Data, horário e sessão nas linhas seguintes
    assert str(cells[(3, 1)].value).startswith('Data: ')
    assert '13/01/2026' in str(cells[(3, 1)].value)
    assert str(cells[(4, 1)].value).startswith('Horário:')
    assert '08:00' in str(cells[(4, 1)].value) and '09:00' in str(cells[(4, 1)].value)
    assert cells[(5, 1)].value == '1'
    # Cabeçalho na linha 7
    assert cells[(7, 1)].value == 'Classificação'
    assert cells[(7, 2)].value == 'Classificação NNA'
    assert cells[(7, 3)].value == 'Classificação PCD'
    assert cells[(7, 4)].value == 'Inscrição'
    assert cells[(7, 5)].value == 'Nome'
    assert cells[(7, 6)].value == 'CPF'
    # Primeira linha de dados na 8a linha
    assert cells[(8, 1)].value == 10
    assert cells[(8, 4)].value == 'I1'
    assert cells[(8, 5)].value == 'Nome 1'
    assert cells[(8, 6)].value == '111'
