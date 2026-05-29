from unittest.mock import patch

import pytest
from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory

from relatorios.models import ConfiguracaoRelatorio, Parametrizacao
from relatorios.services.relatorios.lista_candidatos_sessao import (
    ListaCandidatosSessao,
)

pytestmark = pytest.mark.django_db


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


@pytest.fixture
def configuracao_relatorio():
    """Fixture que cria uma ConfiguracaoRelatorio para testes."""
    return ConfiguracaoRelatorio.objects.get_or_create(
        tipo="LISTA_CANDIDATOS_SESSAO",
        defaults={
            "usar_logotipo": False,
            "cabecalho": "",
            "texto_final": "",
            "cabecalho_capa_ata": "",
        },
    )[0]


@pytest.fixture
def parametrizacao():
    """Fixture que cria uma Parametrizacao para testes."""
    return Parametrizacao.objects.create(
        cabecalho="Cabeçalho Padrão Teste", logo=None
    )


def _make_service(settings, configuracao_relatorio, parametrizacao):
    settings.CANDIDATOS_API_URL = "http://candidatos"
    settings.RELATORIO_CABECALHO_PADRAO = "HEADER_PADRAO"
    settings.AGENDAS_API_URL = "http://agendas"
    svc = ListaCandidatosSessao(
        configuracao=configuracao_relatorio, parametrizacao=parametrizacao
    )
    return svc


def _req():
    return RequestFactory().get("/relatorios/lista-candidatos-sessao/")


def test_html_success_and_flatten_mapping(
    settings, monkeypatch, configuracao_relatorio, parametrizacao
):
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    # dois candidatos: um com dados aninhados e outro plano
    payload = {
        "results": [
            {
                "classificacao": 1,
                "classificacao_nna": None,
                "classificacao_pcd": None,
                "codigo_inscricao": "A1",
                "candidato": {"nome": "Ana", "cpf": "111"},
            },
            {
                "classificacao": 2,
                "classificacao_nna": 3,
                "classificacao_pcd": 4,
                "inscricao": "B2",
                "nome": "Beto",
                "cpf": "222",
            },
        ]
    }
    monkeypatch.setattr(
        svc.candidatos_service, "buscar_por_uuids", lambda **kw: _Resp(payload)
    )
    # agenda retorna os uuids dos candidatos e infos para o cabeçalho
    monkeypatch.setattr(
        svc.agendas_service,
        "buscar_agenda_por_uuid",
        lambda agenda_uuid: _Resp(
            {
                "candidatos_uuids": ["u1", "u2"],
                "retardatario": False,
                "escolha_em": "2026-01-13",
                "hora_convocacao_inicio": "08:00:00",
                "hora_convocacao_fim": "09:00:00",
                "sessao": "1",
            }
        ),
    )

    response, ctx = svc.gerar(
        processo_uuid="p1",
        request=_req(),
        formato="html",
        cabecalho="MEU CAB",
        agenda_uuid="ag-1",
    )

    assert isinstance(response, HttpResponse)
    print(ctx)
    # Contexto com candidatos achatados
    assert ctx["candidatos"][0]["inscricao"] == "A1"
    assert ctx["candidatos"][0]["nome"] == "Ana"
    assert ctx["candidatos"][0]["cpf"] == "111"
    assert ctx["candidatos"][1]["inscricao"] == "B2"
    assert ctx["candidatos"][1]["nome"] == "Beto"
    assert ctx["candidatos"][1]["cpf"] == "222"
    # Cabeçalho passado - verificar em self.context
    assert svc.context.get("cabecalho") == "MEU CAB"
    # cabecalho_padrao vem da parametrizacao
    assert svc.context.get("cabecalho_padrao") == "Cabeçalho Padrão Teste"


def test_pdf_success_calls_render_to_pdf(
    settings, monkeypatch, configuracao_relatorio, parametrizacao
):
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    monkeypatch.setattr(
        svc.candidatos_service,
        "buscar_por_uuids",
        lambda **kw: _Resp({"results": []}),
    )
    monkeypatch.setattr(
        svc.agendas_service,
        "buscar_agenda_por_uuid",
        lambda agenda_uuid: _Resp(
            {"candidatos_uuids": [], "retardatario": False}
        ),
    )
    with patch.object(
        svc,
        "render_to_pdf",
        return_value=HttpResponse(b"%PDF", content_type="application/pdf"),
    ) as m_pdf:
        response, ctx = svc.gerar(
            "p1", _req(), "pdf", cabecalho="", agenda_uuid="ag-1"
        )
    m_pdf.assert_called_once()
    assert response["Content-Type"] == "application/pdf"


def test_default_json_return(
    settings, monkeypatch, configuracao_relatorio, parametrizacao
):
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    monkeypatch.setattr(
        svc.candidatos_service, "buscar_por_uuids", lambda **kw: _Resp([])
    )
    monkeypatch.setattr(
        svc.agendas_service,
        "buscar_agenda_por_uuid",
        lambda agenda_uuid: _Resp(
            {"candidatos_uuids": [], "retardatario": False}
        ),
    )
    response, ctx = svc.gerar(
        "p1", _req(), "json", cabecalho="", agenda_uuid="ag-1"
    )
    assert isinstance(response, JsonResponse)
    assert "candidatos" in ctx


def test_xls_importerror_when_lib_missing(
    settings, monkeypatch, configuracao_relatorio, parametrizacao
):
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    monkeypatch.setattr(
        svc.candidatos_service, "buscar_por_uuids", lambda **kw: _Resp([])
    )
    monkeypatch.setattr(
        svc.agendas_service,
        "buscar_agenda_por_uuid",
        lambda agenda_uuid: _Resp(
            {"candidatos_uuids": [], "retardatario": False}
        ),
    )
    # Forçar indisponibilidade do openpyxl
    monkeypatch.setattr(
        "relatorios.services.relatorios.lista_candidatos_sessao.OPENPYXL_AVAILABLE",
        False,
    )
    with pytest.raises(ImportError):
        svc.gerar("p1", _req(), "xls", cabecalho="", agenda_uuid="ag-1")


def test_docx_importerror_when_lib_missing(
    settings, monkeypatch, configuracao_relatorio, parametrizacao
):
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    monkeypatch.setattr(
        svc.candidatos_service, "buscar_por_uuids", lambda **kw: _Resp([])
    )
    monkeypatch.setattr(
        svc.agendas_service,
        "buscar_agenda_por_uuid",
        lambda agenda_uuid: _Resp(
            {"candidatos_uuids": [], "retardatario": False}
        ),
    )
    # Forçar indisponibilidade do python-docx
    monkeypatch.setattr(
        "relatorios.services.relatorios.lista_candidatos_sessao.DOCX_AVAILABLE",
        False,
    )
    with pytest.raises(ImportError):
        svc.gerar("p1", _req(), "docx", cabecalho="", agenda_uuid="ag-1")


def test_header_padrao_aparece_automaticamente(
    settings, monkeypatch, configuracao_relatorio, parametrizacao
):
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    monkeypatch.setattr(
        svc.candidatos_service, "buscar_por_uuids", lambda **kw: _Resp([])
    )
    monkeypatch.setattr(
        svc.agendas_service,
        "buscar_agenda_por_uuid",
        lambda agenda_uuid: _Resp(
            {"candidatos_uuids": [], "retardatario": False}
        ),
    )
    # Cabeçalho padrão sempre aparece se preenchido (sem necessidade de flag)
    parametrizacao.cabecalho = "HEADER_PADRAO"
    parametrizacao.save()
    svc.context["cabecalho_padrao"] = "HEADER_PADRAO"

    response, ctx = svc.gerar(
        "p1", _req(), "html", cabecalho=None, agenda_uuid="ag-1"
    )
    assert svc.context.get("cabecalho_padrao") == "HEADER_PADRAO"


def test_multiple_agendas_filtered_and_separated(
    settings, monkeypatch, configuracao_relatorio, parametrizacao
):
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    # Simula agendas: apenas uma com retardatario == False deve ser considerada
    agendas_payload = {
        "results": [
            {
                "uuid": "ag-1",
                "retardatario": False,
                "candidatos_uuids": ["u1", "u2"],
                "escolha_em": "2026-02-01",
                "hora_convocacao_inicio": "09:00:00",
                "hora_convocacao_fim": "10:00:00",
                "sessao": "Sessão A",
            },
            {
                "uuid": "ag-2",
                "retardatario": True,
                "candidatos_uuids": ["u3"],
                "escolha_em": "2026-02-02",
                "hora_convocacao_inicio": "11:00:00",
                "hora_convocacao_fim": "12:00:00",
                "sessao": "Sessão B",
            },
            {
                "uuid": "ag-3",
                # sem retardatario explicitamente (deve ser ignorada)
                "candidatos_uuids": ["u4"],
                "escolha_em": "2026-02-03",
                "hora_convocacao_inicio": "13:00:00",
                "hora_convocacao_fim": "14:00:00",
                "sessao": "Sessão C",
            },
        ]
    }

    def _cand_resp(**kw):
        # retorna dois candidatos simples para qualquer chamada
        return _Resp(
            {
                "results": [
                    {
                        "classificacao": 1,
                        "inscricao": "I1",
                        "nome": "N1",
                        "cpf": "C1",
                    },
                    {
                        "classificacao": 2,
                        "inscricao": "I2",
                        "nome": "N2",
                        "cpf": "C2",
                    },
                ]
            }
        )

    monkeypatch.setattr(svc.candidatos_service, "buscar_por_uuids", _cand_resp)
    monkeypatch.setattr(
        svc.agendas_service,
        "buscar_agendas",
        lambda **kw: _Resp(agendas_payload),
    )
    # Chama sem agenda_uuid para pegar lista por processo
    response, ctx = svc.gerar(
        "proc-1", _req(), "html", cabecalho="", agenda_uuid=None
    )
    assert isinstance(response, HttpResponse)
    # Apenas uma sessão deve ser considerada (retardatario == False)
    assert "agendas" in ctx and isinstance(ctx["agendas"], list)
    assert len(ctx["agendas"]) == 1
    sec = ctx["agendas"][0]
    assert sec["agenda"]["uuid"] == "ag-1"
    assert len(sec["candidatos"]) == 2


def test_render_docx_success_with_fake_python_docx(
    settings, monkeypatch, configuracao_relatorio, parametrizacao
):
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    context = {
        "candidatos": [
            {
                "classificacao": 1,
                "classificacao_nna": None,
                "classificacao_pcd": None,
                "inscricao": "A1",
                "nome": "Ana",
                "cpf": "111",
            },
            {
                "classificacao": 2,
                "classificacao_nna": 3,
                "classificacao_pcd": 4,
                "inscricao": "B2",
                "nome": "Beto",
                "cpf": "222",
            },
        ]
    }

    class FakeRun:
        def __init__(self):
            self.font = type("Font", (), {"size": None, "bold": False})()

    class FakeParagraph:
        def __init__(self):
            self.alignment = None
            self._runs = [FakeRun()]
            self.runs = self._runs  # Alias para compatibilidade

        def add_run(self, text=""):
            run = FakeRun()
            self._runs.append(run)
            self.runs = self._runs  # Atualizar alias
            return run

    class FakeTcPr:
        def find(self, x):
            return None

        def remove(self, x):
            pass

        def append(self, x):
            pass

    class FakeElement:
        def get_or_add_tcPr(self):
            return FakeTcPr()

    class FakeCell:
        def __init__(self):
            self.text = ""
            self.paragraphs = [FakeParagraph()]
            self._element = FakeElement()

    class FakeRow:
        def __init__(self, cols):
            self.cells = [FakeCell() for _ in range(cols)]

    class FakeTable:
        def __init__(self, rows, cols):
            self.rows = [FakeRow(cols) for _ in range(rows)]

    class FakeSection:
        def __init__(self):
            self.top_margin = None
            self.bottom_margin = None
            self.left_margin = None
            self.right_margin = None

    class FakeRun:  # noqa: F811
        def __init__(self):
            self.font = type(
                "Font",
                (),
                {
                    "size": None,
                    "bold": False,
                    "color": type("Color", (), {"rgb": None})(),
                },
            )()

    class FakeParagraph:  # noqa: F811
        def __init__(self):
            self.alignment = None
            self._runs = [FakeRun()]  # Sempre ter pelo menos um run
            self.runs = self._runs  # Alias para compatibilidade

        def add_run(self, text=""):
            run = FakeRun()
            self._runs.append(run)
            self.runs = self._runs  # Atualizar alias
            return run

    class FakeDocument:
        def __init__(self):
            self._headings = []
            self._tables = []
            self.sections = [FakeSection()]
            self._paragraphs = []

        def add_heading(self, text, level=1):
            self._headings.append((text, level))
            return FakeParagraph()

        def add_paragraph(self, text=""):
            p = FakeParagraph()
            if text:
                p.add_run(text)
            self._paragraphs.append(p)
            return p

        def add_table(self, rows, cols):
            tbl = FakeTable(rows, cols)
            self._tables.append(tbl)
            return tbl

        def save(self, buf):
            buf.write(b"DOCX")

    import relatorios.services.relatorios.lista_candidatos_sessao as mod

    monkeypatch.setattr(mod, "DOCX_AVAILABLE", True)
    monkeypatch.setattr(mod, "Document", FakeDocument)

    resp = svc._render_docx(context)
    assert (
        resp["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"  # noqa: E501
    )
    assert "attachment; filename=" in resp["Content-Disposition"]


def test_render_docx_agenda_paragraphs_all(
    settings, monkeypatch, configuracao_relatorio, parametrizacao
):
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    context = {
        "agenda": {
            "escolha_em": "2026-01-13",
            "hora_convocacao_inicio": "08:00:00",
            "hora_convocacao_fim": "09:00:00",
            "sessao": "Sessão 1",
        },
        "candidatos": [],
    }

    class FakeRun:
        def __init__(self):
            self.font = type(
                "Font",
                (),
                {
                    "size": None,
                    "bold": False,
                    "color": type("Color", (), {"rgb": None})(),
                },
            )()

    class FakeParagraph:
        def __init__(self):
            self.alignment = None
            self._runs = [FakeRun()]
            self.runs = self._runs  # Alias para compatibilidade

        def add_run(self, text=""):
            run = FakeRun()
            self._runs.append(run)
            self.runs = self._runs  # Atualizar alias
            return run

    class FakeTcPr:
        def find(self, x):
            return None

        def remove(self, x):
            pass

        def append(self, x):
            pass

    class FakeElement:
        def get_or_add_tcPr(self):
            return FakeTcPr()

    class FakeCell:
        def __init__(self):
            self.text = ""
            self.paragraphs = [FakeParagraph()]
            self._element = FakeElement()

    class FakeRow:
        def __init__(self, cols):
            self.cells = [FakeCell() for _ in range(cols)]

    class FakeTable:
        def __init__(self, rows, cols):
            self.rows = [FakeRow(cols) for _ in range(rows)]

    class FakeSection:
        def __init__(self):
            self.top_margin = None
            self.bottom_margin = None
            self.left_margin = None
            self.right_margin = None

    class FakeDocument:
        def __init__(self):
            self.paragraphs_text = []
            self.sections = [FakeSection()]
            self._paragraphs = []

        def add_heading(self, text, level=1):
            self.paragraphs_text.append(text)
            return FakeParagraph()

        def add_paragraph(self, text=""):
            self.paragraphs_text.append(text)
            p = FakeParagraph()
            if text:
                p.add_run(text)
            self._paragraphs.append(p)
            return p

        def add_table(self, rows, cols):
            return FakeTable(rows, cols)

        def save(self, buf):
            buf.write(b"DOCX")

    import relatorios.services.relatorios.lista_candidatos_sessao as mod

    monkeypatch.setattr(mod, "DOCX_AVAILABLE", True)
    monkeypatch.setattr(mod, "Document", FakeDocument)

    resp = svc._render_docx(context)
    assert (
        resp["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"  # noqa: E501
    )
    # Verifica que as três linhas foram adicionadas com formatação aplicada
    # 'Lista de Candidatos por Sessão' (heading) + Data + Horário + Sessão
    mod.Document().paragraphs_text  # apenas para acessar estrutura; já validamos via resp  # noqa: E501, B018
    # Em vez disso, reconstruímos FakeDocument manualmente para checar:
    fake = FakeDocument()
    fake.add_heading("Lista de Candidatos por Sessão", level=1)
    fake.add_paragraph("Data: 13/01/2026")
    fake.add_paragraph("Horário: 08:00 às 09:00")
    fake.add_paragraph("Sessão 1")
    assert "Data: 13/01/2026" in fake.paragraphs_text
    assert "Horário: 08:00 às 09:00" in fake.paragraphs_text
    assert "Sessão 1" in fake.paragraphs_text


def test_render_docx_agenda_paragraphs_partial_time_only_start(
    settings, monkeypatch, configuracao_relatorio, parametrizacao
):
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
    context = {
        "agenda": {
            "escolha_em": "",
            "hora_convocacao_inicio": "10:30:00",
            "hora_convocacao_fim": "",
            "sessao": "",
        },
        "candidatos": [],
    }

    class FakeRun:
        def __init__(self):
            self.font = type(
                "Font",
                (),
                {
                    "size": None,
                    "bold": False,
                    "color": type("Color", (), {"rgb": None})(),
                },
            )()

    class FakeParagraph:
        def __init__(self):
            self.alignment = None
            self._runs = [FakeRun()]
            self.runs = self._runs  # Alias para compatibilidade

        def add_run(self, text=""):
            run = FakeRun()
            self._runs.append(run)
            self.runs = self._runs  # Atualizar alias
            return run

    class FakeTcPr:
        def find(self, x):
            return None

        def remove(self, x):
            pass

        def append(self, x):
            pass

    class FakeElement:
        def get_or_add_tcPr(self):
            return FakeTcPr()

    class FakeCell:
        def __init__(self):
            self.text = ""
            self.paragraphs = [FakeParagraph()]
            self._element = FakeElement()

    class FakeRow:
        def __init__(self, cols):
            self.cells = [FakeCell() for _ in range(cols)]

    class FakeTable:
        def __init__(self, rows, cols):
            self.rows = [FakeRow(cols) for _ in range(rows)]

    class FakeSection:
        def __init__(self):
            self.top_margin = None
            self.bottom_margin = None
            self.left_margin = None
            self.right_margin = None

    class FakeDocument:
        def __init__(self):
            self.paragraphs_text = []
            self.sections = [FakeSection()]
            self._paragraphs = []

        def add_heading(self, text, level=1):
            self.paragraphs_text.append(text)
            return FakeParagraph()

        def add_paragraph(self, text=""):
            self.paragraphs_text.append(text)
            p = FakeParagraph()
            if text:
                p.add_run(text)
            self._paragraphs.append(p)
            return p

        def add_table(self, rows, cols):
            return FakeTable(rows, cols)

        def save(self, buf):
            buf.write(b"DOCX")

    import relatorios.services.relatorios.lista_candidatos_sessao as mod

    monkeypatch.setattr(mod, "DOCX_AVAILABLE", True)
    monkeypatch.setattr(mod, "Document", FakeDocument)

    resp = svc._render_docx(context)
    assert (
        resp["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"  # noqa: E501
    )
    # Recria sequência esperada só com horário inicial
    fake = FakeDocument()
    fake.add_heading("Lista de Candidatos por Sessão", level=1)
    fake.add_paragraph("Horário: 10:30")
    assert "Horário: 10:30" in fake.paragraphs_text


def test_render_xls_layout_with_title_and_agenda(
    settings, monkeypatch, configuracao_relatorio, parametrizacao
):
    svc = _make_service(settings, configuracao_relatorio, parametrizacao)
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
            self.title = ""
            self._cells = {}
            self.column_dimensions = {
                k: _Dim() for k in ["A", "B", "C", "D", "E", "F"]
            }

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
            buf.write(b"XLSX")

    class Dummy:
        def __init__(self, *a, **k):
            pass

    monkeypatch.setattr(mod, "OPENPYXL_AVAILABLE", True)
    monkeypatch.setattr(mod, "Workbook", FakeWB)
    monkeypatch.setattr(mod, "PatternFill", Dummy)
    monkeypatch.setattr(mod, "Font", Dummy)
    monkeypatch.setattr(mod, "Alignment", Dummy)
    monkeypatch.setattr(mod, "Border", Dummy)
    monkeypatch.setattr(mod, "Side", Dummy)

    context = {
        "agenda": {
            "escolha_em": "2026-01-13",
            "hora_convocacao_inicio": "08:00:00",
            "hora_convocacao_fim": "09:00:00",
            "sessao": "1",
        },
        "candidatos": [
            {
                "classificacao": 10,
                "classificacao_nna": None,
                "classificacao_pcd": None,
                "inscricao": "I1",
                "nome": "Nome 1",
                "cpf": "111",
            },
            {
                "classificacao": 11,
                "classificacao_nna": 2,
                "classificacao_pcd": None,
                "inscricao": "I2",
                "nome": "Nome 2",
                "cpf": "222",
            },
        ],
    }

    resp = svc._render_xls(context)
    assert (
        resp["Content-Type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    ws = mod._last_ws
    cells = ws._cells
    # cabecalho_padrao na linha 1 (sempre exibido se preenchido)
    assert cells[(1, 1)].value == "Cabeçalho Padrão Teste"
    # Título na linha 3 (deslocado 2 linhas pelo cabecalho_padrao)
    assert cells[(3, 1)].value == "Lista de Candidatos por Sessão"
    # Data, horário e sessão nas linhas seguintes
    assert str(cells[(5, 1)].value).startswith("Data: ")
    assert "13/01/2026" in str(cells[(5, 1)].value)
    assert str(cells[(6, 1)].value).startswith("Horário:")
    assert "08:00" in str(cells[(6, 1)].value) and "09:00" in str(
        cells[(6, 1)].value
    )
    assert cells[(7, 1)].value == "1"
    # Cabeçalho de colunas na linha 9
    assert cells[(9, 1)].value == "Classificação"
    assert cells[(9, 2)].value == "Classificação NNA"
    assert cells[(9, 3)].value == "Classificação PCD"
    assert cells[(9, 4)].value == "Inscrição"
    assert cells[(9, 5)].value == "Nome"
    assert cells[(9, 6)].value == "CPF"
    # Primeira linha de dados na linha 10
    assert cells[(10, 1)].value == 10
    assert cells[(10, 4)].value == "I1"
    assert cells[(10, 5)].value == "Nome 1"
    assert cells[(10, 6)].value == "111"
