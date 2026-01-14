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

    response, ctx = svc.gerar(
        processo_uuid='p1',
        request=_req(),
        formato='html',
        cabecalho='MEU CAB',
        candidatos_uuids=['u1', 'u2'],
    )

    assert isinstance(response, HttpResponse)
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
    with patch.object(svc, 'render_to_pdf', return_value=HttpResponse(b'%PDF', content_type='application/pdf')) as m_pdf:
        response, ctx = svc.gerar('p1', _req(), 'pdf', cabecalho='', candidatos_uuids=['x'])
    m_pdf.assert_called_once()
    assert response['Content-Type'] == 'application/pdf'


def test_default_json_return(settings, monkeypatch):
    svc = _make_service(settings)
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp([]))
    response, ctx = svc.gerar('p1', _req(), 'json', cabecalho='')
    assert isinstance(response, JsonResponse)
    assert 'candidatos' in ctx


def test_xls_importerror_when_lib_missing(settings, monkeypatch):
    svc = _make_service(settings)
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp([]))
    # Forçar indisponibilidade do openpyxl
    monkeypatch.setattr('relatorios.services.relatorios.lista_candidatos_sessao.OPENPYXL_AVAILABLE', False)
    with pytest.raises(ImportError):
        svc.gerar('p1', _req(), 'xls', cabecalho='')


def test_docx_importerror_when_lib_missing(settings, monkeypatch):
    svc = _make_service(settings)
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp([]))
    # Forçar indisponibilidade do python-docx
    monkeypatch.setattr('relatorios.services.relatorios.lista_candidatos_sessao.DOCX_AVAILABLE', False)
    with pytest.raises(ImportError):
        svc.gerar('p1', _req(), 'docx', cabecalho='')


def test_header_fallback_uses_settings_default(settings, monkeypatch):
    svc = _make_service(settings)
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp([]))
    response, ctx = svc.gerar('p1', _req(), 'html', cabecalho=None)
    assert ctx['cabecalho'] == 'HEADER_PADRAO'


def test_render_xls_success_with_fake_openpyxl(settings, monkeypatch):
    svc = _make_service(settings)
    context = {
        'candidatos': [
            {'classificacao': 1, 'classificacao_nna': None, 'classificacao_pcd': None, 'inscricao': 'A1', 'nome': 'Ana', 'cpf': '111'},
            {'classificacao': 2, 'classificacao_nna': 3, 'classificacao_pcd': 4, 'inscricao': 'B2', 'nome': 'Beto', 'cpf': '222'},
        ]
    }

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

    class FakeWB:
        def __init__(self):
            self.active = FakeWS()
        def save(self, buf):
            # escreve bytes simulando arquivo xlsx
            buf.write(b'XLSX')

    class Dummy:  # para PatternFill, Font, Alignment, Border, Side
        def __init__(self, *a, **k):
            pass

    import relatorios.services.relatorios.lista_candidatos_sessao as mod
    monkeypatch.setattr(mod, 'OPENPYXL_AVAILABLE', True)
    monkeypatch.setattr(mod, 'Workbook', FakeWB)
    monkeypatch.setattr(mod, 'PatternFill', Dummy)
    monkeypatch.setattr(mod, 'Font', Dummy)
    monkeypatch.setattr(mod, 'Alignment', Dummy)
    monkeypatch.setattr(mod, 'Border', Dummy)
    monkeypatch.setattr(mod, 'Side', Dummy)

    resp = svc._render_xls(context)
    assert resp['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    assert 'attachment; filename=' in resp['Content-Disposition']


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

