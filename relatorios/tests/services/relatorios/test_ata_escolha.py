from unittest.mock import Mock, patch

import pytest
from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory

from relatorios.models import ConfiguracaoRelatorio, Parametrizacao
from relatorios.services.relatorios.ata_escolha import (
    DOCX_AVAILABLE,
    OPENPYXL_AVAILABLE,
    AtaEscolha,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def configuracao_relatorio():
    """Fixture que cria uma ConfiguracaoRelatorio para testes."""
    return ConfiguracaoRelatorio.objects.get_or_create(
        tipo="ATA_ESCOLHA",
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


@pytest.fixture
def settings_config(settings):
    """Configuração padrão de settings para os testes."""
    settings.CANDIDATOS_API_URL = "http://candidatos"
    settings.CONVOCACAO_API_URL = "http://processos"
    settings.AGENDAS_API_URL = "http://agendas"
    settings.ESCOLHAS_API_URL = "http://escolhas"
    settings.RELATORIO_CABECALHO_PADRAO = "CABECALHO_PADRAO"
    return settings


@pytest.fixture
def service(settings_config, configuracao_relatorio, parametrizacao):
    """Fixture para criar instância de AtaEscolha."""
    return AtaEscolha(
        configuracao=configuracao_relatorio, parametrizacao=parametrizacao
    )


@pytest.fixture
def service_mocked(service):
    """Fixture para criar serviço com mock do ata_service."""
    service.ata_service = Mock()
    return service


@pytest.fixture
def dados_ata():
    """Dados de exemplo para a ata de escolha."""
    return {
        "processo_uuid": "proc-123",
        "concurso_uuid": "conc-456",
        "total_cargos": 1,
        "cargos": [
            {
                "cargo_nome": "Professor",
                "cargo_codigo": "123",
                "numero_sessoes": 1,
                "sessoes": [
                    {
                        "numero_sessao": 1,
                        "hora_convocacao_inicio": "09:00",
                        "hora_convocacao_fim": "10:00",
                        "horario_formatado": "09:00 às 10:00",
                        "total_candidatos": 2,
                        "candidatos": [
                            {
                                "uuid": "cand-1",
                                "classificacao": 1,
                                "classificacao_pcd": None,
                                "classificacao_nna": None,
                                "nome": "Candidato Um",
                                "rg": "1234567",
                                "cpf": "11111111111",
                                "rf": "RF001",
                                "codigo_eol": "12345",
                                "dre_codigo": "DRE-A",
                                "dre_nome": "DRE A",
                                "tipo_unidade": "EMEF",
                                "nome_escola_escolhida": "Escola Teste",
                                "tipo_vaga": "P",
                                "assinatura": "Escolha",
                                "candidato": {
                                    "nome": "Candidato Um",
                                    "rg": "1234567",
                                    "cpf": "11111111111",
                                    "registro_funcional": "RF001",
                                },
                            },
                            {
                                "uuid": "cand-2",
                                "classificacao": 2,
                                "classificacao_pcd": None,
                                "classificacao_nna": None,
                                "nome": "Candidato Dois",
                                "rg": "7654321",
                                "cpf": "22222222222",
                                "rf": "RF002",
                                "codigo_eol": "",
                                "dre_codigo": "",
                                "dre_nome": "",
                                "tipo_unidade": "",
                                "nome_escola_escolhida": "",
                                "tipo_vaga": "",
                                "assinatura": "Não Escolha",
                                "candidato": {
                                    "nome": "Candidato Dois",
                                    "rg": "7654321",
                                    "cpf": "22222222222",
                                    "registro_funcional": "RF002",
                                },
                            },
                        ],
                    }
                ],
            }
        ],
    }


@pytest.fixture
def request_obj():
    """Fixture para criar objeto de request."""
    return RequestFactory().get("/relatorios/ata-escolha/")


def _make_cargo_list(**kwargs):
    """Helper para criar lista de cargos com diferentes variações."""
    cargo_base = {
        "cargo_nome": kwargs.get("cargo_nome", "Professor"),
        "cargo_codigo": kwargs.get("cargo_codigo", "123"),
        "sessoes": kwargs.get(
            "sessoes",
            [
                {
                    "numero_sessao": 1,
                    "horario_formatado": kwargs.get(
                        "horario_formatado", "09:00 às 10:00"
                    ),
                    "candidatos": kwargs.get("candidatos", []),
                }
            ],
        ),
    }
    return (
        [cargo_base]
        if not kwargs.get("multiplos_cargos")
        else [
            cargo_base,
            {
                "cargo_nome": "Coordenador",
                "cargo_codigo": "456",
                "sessoes": [
                    {
                        "numero_sessao": 1,
                        "horario_formatado": "11:00 às 12:00",
                        "candidatos": kwargs.get("candidatos", []),
                    }
                ],
            },
        ]
    )


def test_init(settings_config, configuracao_relatorio, parametrizacao):
    """Testa inicialização da classe AtaEscolha."""
    svc = AtaEscolha(
        configuracao=configuracao_relatorio, parametrizacao=parametrizacao
    )
    assert svc.ata_service is not None
    assert svc.TEMPLATE_NAME == "relatorios/ata_escolha.html"


@pytest.mark.parametrize(
    "formato,cabecalho,expected_method,expected_content_type,expected_filename",
    [
        ("html", "CABECALHO_TESTE", "render", None, None),
        (
            "pdf",
            "CABECALHO",
            "render_to_pdf",
            "application/pdf",
            "ata_escolha_proc-123.pdf",
        ),
        (
            "docx",
            "CABECALHO",
            "render_to_docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "ata_escolha_proc-123.docx",
        ),
        ("doc", "CABECALHO", "render_to_docx", None, None),
        (
            "xlsx",
            "CABECALHO",
            "_render_xls",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "ata_escolha_proc-123.xlsx",
        ),
        ("xls", "CABECALHO", "_render_xls", None, None),
        ("json", "CABECALHO", None, None, None),
    ],
)
def test_gerar_formatos(
    settings_config,
    service_mocked,
    dados_ata,
    request_obj,
    formato,
    cabecalho,
    expected_method,
    expected_content_type,
    expected_filename,
):
    """Testa geração de relatório em diferentes formatos."""
    service_mocked.ata_service.processar_ata_escolha.return_value = dados_ata

    if formato == "html":
        with patch(
            "relatorios.services.relatorios.ata_escolha.render",
            return_value=HttpResponse("OK"),
        ) as m_render:
            response, dados = service_mocked.gerar(
                processo_uuid="proc-123",
                request=request_obj,
                formato=formato,
                cabecalho=cabecalho,
            )
        assert isinstance(response, HttpResponse)
        m_render.assert_called_once()
        context = (
            m_render.call_args[0][2]
            if len(m_render.call_args[0]) >= 3
            else m_render.call_args[1].get("context")
        )
        assert context["cargos"] == dados_ata["cargos"]
        # O cabeçalho é processado pelo método gerar
        if cabecalho and cabecalho.strip():
            assert context["cabecalho"] == cabecalho.strip()
        else:
            # Usa cabeçalho padrão se vazio
            assert (
                context["cabecalho"] == ""
                or context["cabecalho"] == "CABECALHO_PADRAO"
            )
    elif formato == "pdf":
        with patch.object(
            service_mocked,
            "render_to_pdf",
            return_value=HttpResponse(
                b"%PDF-1.4", content_type=expected_content_type
            ),
        ) as m_pdf:
            response, dados = service_mocked.gerar(
                processo_uuid="proc-123",
                request=request_obj,
                formato=formato,
                cabecalho=cabecalho,
            )
        m_pdf.assert_called_once()
        assert m_pdf.call_args[0][0] == "relatorios/ata_escolha.html"
        assert m_pdf.call_args[0][1]["cargos"] == dados_ata["cargos"]
        assert m_pdf.call_args[1]["filename"] == expected_filename
    elif formato in ("docx", "doc"):
        mock_response = HttpResponse(
            b"DOCX",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        mock_response["Content-Disposition"] = (
            'attachment; filename="ata_escolha_proc-123.docx"'
        )
        with patch.object(
            service_mocked, "render_to_docx", return_value=mock_response
        ) as m_docx:
            response, dados = service_mocked.gerar(
                processo_uuid="proc-123",
                request=request_obj,
                formato=formato,
                cabecalho=cabecalho,
            )
        m_docx.assert_called_once()
        assert isinstance(response, HttpResponse)
        if expected_filename:
            assert (
                expected_filename in response["Content-Disposition"]
                or "ata_escolha" in response["Content-Disposition"]
            )
    elif formato in ("xlsx", "xls"):
        with patch.object(
            service_mocked,
            "_render_xls",
            return_value=HttpResponse(
                b"XLSX",
                content_type=expected_content_type
                or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # noqa: E501
            ),
        ) as m_xls:
            response, dados = service_mocked.gerar(
                processo_uuid="proc-123",
                request=request_obj,
                formato=formato,
                cabecalho=cabecalho,
            )
        m_xls.assert_called_once()
        # _render_xls recebe context_data como primeiro argumento
        context_passed = m_xls.call_args[0][0]
        assert context_passed["cargos"] == dados_ata["cargos"]
        # Verificar se o cabeçalho está no contexto
        if cabecalho and cabecalho.strip():
            assert context_passed["cabecalho"] == cabecalho.strip()
        # Verificar filename
        if expected_filename:
            assert (
                m_xls.call_args[1]["filename"] == expected_filename
                or "ata_escolha" in m_xls.call_args[1]["filename"]
            )
    elif formato == "json":
        response, dados = service_mocked.gerar(
            processo_uuid="proc-123",
            request=request_obj,
            formato=formato,
            cabecalho=cabecalho,
        )
        assert isinstance(response, JsonResponse)

    assert isinstance(response, HttpResponse)
    assert dados == dados_ata


def test_gerar_html_uses_cabecalho_padrao_quando_vazio(
    settings_config, service_mocked, dados_ata, request_obj
):
    """
    Testa que usa cabecalho_padrao da Parametrizacao quando cabecalho está
    vazio.
    """
    service_mocked.context["cabecalho_padrao"] = "CABECALHO_PADRAO"
    service_mocked.ata_service.processar_ata_escolha.return_value = dados_ata
    with patch(
        "relatorios.services.relatorios.ata_escolha.render",
        return_value=HttpResponse("OK"),
    ) as m_render:
        service_mocked.gerar(
            processo_uuid="proc-123",
            request=request_obj,
            formato="html",
            cabecalho="",
        )
    context = (
        m_render.call_args[0][2]
        if len(m_render.call_args[0]) >= 3
        else m_render.call_args[1].get("context")
    )
    assert context["cabecalho_padrao"] == "CABECALHO_PADRAO"


@pytest.mark.parametrize(
    "cabecalho,esperado",
    [
        ("  CABECALHO  ", "CABECALHO"),
        (None, "Cabeçalho Padrão Teste"),
    ],
)
def test_gerar_cabecalho_tratamento(
    settings_config,
    service_mocked,
    dados_ata,
    request_obj,
    cabecalho,
    esperado,
):
    """
    Testa tratamento de cabeçalho (stripped) e uso de cabecalho_padrao quando
    vazio.
    """
    service_mocked.ata_service.processar_ata_escolha.return_value = dados_ata
    with patch(
        "relatorios.services.relatorios.ata_escolha.render",
        return_value=HttpResponse("OK"),
    ) as m_render:
        service_mocked.gerar(
            processo_uuid="proc-123",
            request=request_obj,
            formato="html",
            cabecalho=cabecalho,
        )
    context = (
        m_render.call_args[0][2]
        if len(m_render.call_args[0]) >= 3
        else m_render.call_args[1].get("context")
    )
    if cabecalho and cabecalho.strip():
        assert context["cabecalho"] == esperado
    else:
        assert context["cabecalho_padrao"] == esperado


def test_gerar_raises_exception_on_service_failure(
    settings_config, service_mocked, request_obj
):
    """Testa que exceção é levantada quando o serviço falha."""
    service_mocked.ata_service.processar_ata_escolha.side_effect = Exception(
        "Falha no serviço"
    )
    with pytest.raises(Exception, match="Falha no serviço"):
        service_mocked.gerar(
            processo_uuid="proc-123",
            request=request_obj,
            formato="html",
            cabecalho="",
        )


def test_gerar_processo_uuid_none(
    settings_config, service_mocked, dados_ata, request_obj
):
    """Testa geração com processo_uuid None."""
    service_mocked.ata_service.processar_ata_escolha.return_value = dados_ata
    with patch(
        "relatorios.services.relatorios.ata_escolha.render",
        return_value=HttpResponse("OK"),
    ):
        service_mocked.gerar(
            processo_uuid=None, request=request_obj, formato="html"
        )
    service_mocked.ata_service.processar_ata_escolha.assert_called_once_with(
        processo_uuid="",
        cargo_codigo=None,
    )


@pytest.mark.skipif(
    not DOCX_AVAILABLE, reason="python-docx não está instalado"
)
@pytest.mark.parametrize(
    "cabecalho,cargos_list",
    [
        ("CABECALHO TESTE", None),  # None usa dados_ata['cargos']
        ("", None),
        (
            "CABECALHO",
            {
                "candidatos": [
                    {
                        "classificacao": 1,
                        "status_especial": "CANDIDATOS JÁ CLASSIFICADO.",
                        "codigo_eol": "",
                        "dre_codigo": "",
                        "tipo_unidade": "",
                        "nome_escola_escolhida": "",
                        "tipo_vaga": "",
                        "assinatura": "Não Escolha",
                        "candidato": {},
                    }
                ]
            },
        ),
        (
            "CABECALHO",
            {
                "candidatos": [
                    {
                        "classificacao": 1,
                        "nome": "Nome Direto",
                        "rf": "RF001",
                        "rg": "123456",
                        "cpf": "11111111111",
                        "codigo_eol": "12345",
                        "dre_codigo": "DRE-A",
                        "tipo_unidade": "EMEF",
                        "nome_escola_escolhida": "Escola",
                        "tipo_vaga": "P",
                        "assinatura": "Escolha",
                    }
                ]
            },
        ),
        (
            "CABECALHO",
            {
                "candidatos": [
                    {
                        "classificacao": None,
                        "classificacao_pcd": None,
                        "classificacao_nna": None,
                        "nome": "Candidato",
                        "rf": "RF001",
                        "rg": "123456",
                        "cpf": "11111111111",
                        "codigo_eol": "",
                        "dre_codigo": "",
                        "tipo_unidade": "",
                        "nome_escola_escolhida": "",
                        "tipo_vaga": "",
                        "assinatura": "Não Escolha",
                        "candidato": {},
                    }
                ]
            },
        ),
        (
            "CABECALHO",
            {
                "multiplos_cargos": True,
                "candidatos": [
                    {
                        "classificacao": 1,
                        "nome": "Candidato 1",
                        "rf": "RF001",
                        "rg": "123456",
                        "cpf": "11111111111",
                        "codigo_eol": "",
                        "dre_codigo": "",
                        "tipo_unidade": "",
                        "nome_escola_escolhida": "",
                        "tipo_vaga": "",
                        "assinatura": "Não Escolha",
                        "candidato": {},
                    }
                ],
            },
        ),
        ("CABECALHO", {"horario_formatado": "", "candidatos": []}),
        ("CABECALHO", {"candidatos": []}),
    ],
)
def test_render_to_docx_variacoes(
    settings_config, service, dados_ata, cabecalho, cargos_list
):
    """Testa geração de DOCX com diferentes variações de dados."""
    cargos = (
        _make_cargo_list(**(cargos_list or {}))
        if cargos_list
        else dados_ata["cargos"]
    )
    response = service.render_to_docx(
        cargos, {"cabecalho": cabecalho}, filename="test.docx"
    )
    assert isinstance(response, HttpResponse)
    assert hasattr(response, "content")
    if cabecalho == "CABECALHO TESTE":
        assert (
            response["Content-Type"]
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"  # noqa: E501
        )
        assert (
            'attachment; filename="test.docx"'
            in response["Content-Disposition"]
        )


@pytest.mark.skipif(DOCX_AVAILABLE, reason="python-docx está instalado")
def test_render_to_docx_raises_import_error_when_not_available(
    configuracao_relatorio, parametrizacao
):
    """
    Testa que ImportError é levantado quando python-docx não está disponível.
    """
    with patch(
        "relatorios.services.relatorios.ata_escolha.DOCX_AVAILABLE", False
    ):
        svc = AtaEscolha(
            configuracao=configuracao_relatorio, parametrizacao=parametrizacao
        )
        with pytest.raises(
            ImportError, match="python-docx não está instalado"
        ):
            svc.render_to_docx([], "CABECALHO", filename="test.docx")


@pytest.mark.skipif(
    not OPENPYXL_AVAILABLE, reason="openpyxl não está instalado"
)
@pytest.mark.parametrize(
    "cabecalho,cargos_list,check_content_type",
    [
        ("CABECALHO TESTE", None, True),
        ("", None, False),
        (
            "CABECALHO",
            {
                "candidatos": [
                    {
                        "classificacao": 1,
                        "status_especial": "CANDIDATOS JÁ CLASSIFICADO.",
                        "codigo_eol": "",
                        "dre_codigo": "",
                        "tipo_unidade": "",
                        "nome_escola_escolhida": "",
                        "tipo_vaga": "",
                        "assinatura": "Não Escolha",
                        "candidato": {},
                    }
                ]
            },
            False,
        ),
        (
            "CABECALHO",
            {
                "candidatos": [
                    {
                        "classificacao": 1,
                        "nome": "Nome Direto",
                        "rf": "RF001",
                        "rg": "123456",
                        "cpf": "11111111111",
                        "codigo_eol": "12345",
                        "dre_codigo": "DRE-A",
                        "tipo_unidade": "EMEF",
                        "nome_escola_escolhida": "Escola",
                        "tipo_vaga": "P",
                        "assinatura": "Escolha",
                    }
                ]
            },
            False,
        ),
        (
            "CABECALHO",
            {
                "candidatos": [
                    {
                        "classificacao": None,
                        "classificacao_pcd": None,
                        "classificacao_nna": None,
                        "nome": "Candidato",
                        "rf": "RF001",
                        "rg": "123456",
                        "cpf": "11111111111",
                        "codigo_eol": "",
                        "dre_codigo": "",
                        "tipo_unidade": "",
                        "nome_escola_escolhida": "",
                        "tipo_vaga": "",
                        "assinatura": "Não Escolha",
                        "candidato": {},
                    }
                ]
            },
            False,
        ),
        (
            "CABECALHO",
            {
                "multiplos_cargos": True,
                "candidatos": [
                    {
                        "classificacao": 1,
                        "nome": "Candidato 1",
                        "rf": "RF001",
                        "rg": "123456",
                        "cpf": "11111111111",
                        "codigo_eol": "",
                        "dre_codigo": "",
                        "tipo_unidade": "",
                        "nome_escola_escolhida": "",
                        "tipo_vaga": "",
                        "assinatura": "Não Escolha",
                        "candidato": {},
                    }
                ],
            },
            False,
        ),
        ("CABECALHO", {"horario_formatado": "", "candidatos": []}, False),
        ("CABECALHO", {"candidatos": []}, False),
        ("CABECALHO", {"sessoes": []}, False),
        ("CABECALHO", "empty_list", False),  # Lista vazia de cargos
    ],
)
def test_render_xls_variacoes(
    settings_config,
    service,
    dados_ata,
    cabecalho,
    cargos_list,
    check_content_type,
):
    """Testa geração de XLSX com diferentes variações de dados."""
    if cargos_list == "empty_list":
        cargos = []
    elif cargos_list == {"sessoes": []}:
        cargos = [
            {"cargo_nome": "Professor", "cargo_codigo": "123", "sessoes": []}
        ]
    elif cargos_list is None:
        cargos = dados_ata["cargos"]
    else:
        cargos = _make_cargo_list(**(cargos_list or {}))

    # _render_xls recebe context_data como primeiro argumento
    context_data = service.context.copy()
    context_data["cargos"] = cargos
    context_data["cabecalho"] = cabecalho
    response = service._render_xls(context_data, filename="test.xlsx")
    assert isinstance(response, HttpResponse)
    assert len(response.content) > 0
    if check_content_type:
        assert (
            response["Content-Type"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"  # noqa: E501
        )
        assert (
            'attachment; filename="test.xlsx"'
            in response["Content-Disposition"]
        )


@pytest.mark.skipif(OPENPYXL_AVAILABLE, reason="openpyxl está instalado")
def test_render_xls_raises_import_error_when_not_available(
    configuracao_relatorio, parametrizacao
):
    """
    Testa que ImportError é levantado quando openpyxl não está disponível.
    """
    with patch(
        "relatorios.services.relatorios.ata_escolha.OPENPYXL_AVAILABLE", False
    ):
        svc = AtaEscolha(
            configuracao=configuracao_relatorio, parametrizacao=parametrizacao
        )
        context_data = svc.context.copy()
        context_data["cargos"] = []
        context_data["cabecalho"] = "CABECALHO"
        with pytest.raises(ImportError, match="openpyxl não está instalado"):
            svc._render_xls(context_data, filename="test.xlsx")


@pytest.mark.skipif(
    not DOCX_AVAILABLE, reason="python-docx não está instalado"
)
def test_render_to_docx_exception_handling(
    settings_config, service, dados_ata
):
    """Testa tratamento de exceção em render_to_docx."""
    with patch(  # noqa: SIM117
        "relatorios.services.relatorios.ata_escolha.Document",
        side_effect=Exception("Erro ao criar documento"),
    ):
        with pytest.raises(Exception, match="Erro ao criar documento"):
            service.render_to_docx(
                dados_ata["cargos"], "CABECALHO", filename="test.docx"
            )


@pytest.mark.skipif(
    not OPENPYXL_AVAILABLE, reason="openpyxl não está instalado"
)
def test_render_xls_exception_handling(settings_config, service, dados_ata):
    """Testa tratamento de exceção em _render_xls."""
    context_data = service.context.copy()
    context_data["cargos"] = dados_ata["cargos"]
    context_data["cabecalho"] = "CABECALHO"
    with patch(  # noqa: SIM117
        "relatorios.services.relatorios.ata_escolha.Workbook",
        side_effect=Exception("Erro ao criar workbook"),
    ):
        with pytest.raises(Exception, match="Erro ao criar workbook"):
            service._render_xls(context_data, filename="test.xlsx")
