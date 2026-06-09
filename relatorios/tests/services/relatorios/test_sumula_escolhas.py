"""Testes unitários para o serviço SumulaEscolhas."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from relatorios.models import ConfiguracaoRelatorio, Parametrizacao
from relatorios.services.relatorios.sumula_escolhas import SumulaEscolhas

pytestmark = pytest.mark.django_db


@pytest.fixture
def configuracao_relatorio() -> Any:
    """Fixture que cria uma ConfiguracaoRelatorio para testes."""
    return ConfiguracaoRelatorio.objects.get_or_create(
        tipo="SUMULA_ESCOLHAS",
        defaults={
            "usar_logotipo": False,
            "cabecalho": "",
            "texto_final": "",
            "cabecalho_capa_ata": "",
        },
    )[0]


@pytest.fixture
def parametrizacao() -> Any:
    """Fixture que cria uma Parametrizacao para testes."""
    return Parametrizacao.objects.create(
        cabecalho="Cabeçalho Padrão Teste", logo=None
    )


def _make_request() -> Any:
    """Cria um request mock para os testes."""
    return RequestFactory().get("/relatorios/sumula-escolhas/")


class _MockResponse:
    """Classe auxiliar para mockar respostas HTTP."""

    def __init__(self, json_data: Any, status_code: Any = 200) -> None:
        """Executa   init  ."""
        self._json_data = json_data
        self.status_code = status_code

    def json(self) -> Any:
        """Executa json."""
        return self._json_data


@pytest.fixture
def mock_cargos_response() -> Any:
    """Fixture com dados mockados de cargos."""
    return _MockResponse(
        [
            {
                "cargo_codigo": "123",
                "cargo_nome": "Professor de Educação Infantil",
            },
            {"codigo_cargo": "456", "nome": "Professor de Matemática"},
        ]
    )


@pytest.fixture
def mock_candidatos_response() -> Any:
    """Fixture com dados mockados de candidatos."""
    return _MockResponse(
        {
            "results": [
                {
                    "uuid": "candidato-uuid-1",
                    "codigo_cargo": "123",
                    "descricao_cargo": "Professor de Educação Infantil",
                    "classificacao": 1,
                    "candidato": {
                        "nome": "João Silva",
                        "rg": "123456789",
                        "cpf": "12345678901",
                    },
                },
                {
                    "uuid": "candidato-uuid-2",
                    "codigo_cargo": "123",
                    "descricao_cargo": "Professor de Educação Infantil",
                    "classificacao": 2,
                    "candidato": {
                        "nome": "Maria Santos",
                        "rg": "987654321",
                        "cpf": "98765432109",
                    },
                },
            ]
        }
    )


@pytest.fixture
def mock_escolhas_response() -> Any:
    """Fixture com dados mockados de escolhas."""
    return [
        {
            "candidato_uuid": "candidato-uuid-1",
            "situacao": "escolha",
            "tipo_vaga": "definitiva",
            "vaga_escola": {
                "escola": {
                    "nome_oficial": "EMEF Teste",
                    "codigo_eol": "12345",
                    "dre": {"codigo": "DRE001", "nome": "DRE Butantã"},
                }
            },
        },
        {
            "candidato_uuid": "candidato-uuid-2",
            "situacao": "escolha",
            "tipo_vaga": "precaria",
            "vaga_escola": {
                "escola": {
                    "nome_oficial": "EMEF Teste 2",
                    "codigo_eol": "12346",
                    "dre": {"codigo": "DRE001", "nome": "DRE Butantã"},
                }
            },
        },
        {
            "candidato_uuid": "candidato-uuid-1",
            "situacao": "nao-escolha",
            "tipo_vaga": "definitiva",
            "vaga_escola": {
                "escola": {
                    "nome_oficial": "EMEF Teste 3",
                    "codigo_eol": "12347",
                    "dre": {"codigo": "DRE002", "nome": "DRE Centro"},
                }
            },
        },
    ]


@pytest.fixture
def sumula_escolhas_service(
    settings: Any, configuracao_relatorio: Any, parametrizacao: Any
) -> Any:
    """Fixture que cria uma instância do serviço com mocks."""
    settings.ESCOLHAS_API_URL = "http://escolhas"
    settings.CANDIDATOS_API_URL = "http://candidatos"
    settings.PROCESSOS_API_URL = "http://processos"
    settings.RELATORIO_CABECALHO_PADRAO = "Cabeçalho Padrão"
    service = SumulaEscolhas(
        configuracao=configuracao_relatorio, parametrizacao=parametrizacao
    )
    service.escolhas_service = Mock()
    service.candidatos_service = Mock()
    service.processos_service = Mock()
    return service


class TestInit:
    """Testes para o método __init__."""

    def test_init_com_kwargs(
        self, settings: Any, configuracao_relatorio: Any, parametrizacao: Any
    ) -> None:
        """Testa inicialização com kwargs."""
        settings.ESCOLHAS_API_URL = "http://escolhas"
        settings.CANDIDATOS_API_URL = "http://candidatos"
        settings.PROCESSOS_API_URL = "http://processos"
        service = SumulaEscolhas(
            configuracao=configuracao_relatorio,
            parametrizacao=parametrizacao,
            extra_param="value",
        )
        assert service.escolhas_service is not None
        assert service.candidatos_service is not None
        assert service.processos_service is not None


class TestGerar:
    """Testes para o método gerar."""

    def test_gerar_html_success(
        self,
        sumula_escolhas_service: Any,
        mock_cargos_response: Any,
        mock_candidatos_response: Any,
        mock_escolhas_response: Any,
    ) -> None:
        """Testa geração de relatório HTML com sucesso."""
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response  # noqa: E501
        with patch(
            "relatorios.services.relatorios.sumula_escolhas.render",
            return_value=HttpResponse("OK"),
        ) as m_render:
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
                cabecalho="Cabeçalho Teste",
            )
        assert isinstance(response, HttpResponse)
        m_render.assert_called_once()
        assert len(dados) > 0

    def test_gerar_pdf_success(
        self,
        sumula_escolhas_service: Any,
        mock_cargos_response: Any,
        mock_candidatos_response: Any,
        mock_escolhas_response: Any,
    ) -> None:
        """Testa geração de relatório PDF com sucesso."""
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response  # noqa: E501
        with patch.object(
            sumula_escolhas_service,
            "render_to_pdf",
            return_value=HttpResponse(
                b"%PDF-1.4", content_type="application/pdf"
            ),
        ) as m_pdf:
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="pdf",
                cabecalho="Cabeçalho Teste",
            )
        assert isinstance(response, HttpResponse)
        assert response["Content-Type"] == "application/pdf"
        m_pdf.assert_called_once()

    def test_gerar_xls_success(
        self,
        sumula_escolhas_service: Any,
        mock_cargos_response: Any,
        mock_candidatos_response: Any,
        mock_escolhas_response: Any,
    ) -> None:
        """Testa geração de relatório XLS com sucesso."""
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response  # noqa: E501
        with patch.object(
            sumula_escolhas_service,
            "render_to_xls",
            return_value=HttpResponse(
                b"xlsx",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        ) as m_xls:
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="xls",
                cabecalho="Cabeçalho Teste",
            )
        assert isinstance(response, HttpResponse)
        m_xls.assert_called_once()

    def test_gerar_docx_success(
        self,
        sumula_escolhas_service: Any,
        mock_cargos_response: Any,
        mock_candidatos_response: Any,
        mock_escolhas_response: Any,
    ) -> None:
        """Testa geração de relatório DOCX com sucesso."""
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response  # noqa: E501
        with patch.object(
            sumula_escolhas_service,
            "render_to_docx",
            return_value=HttpResponse(
                b"docx",
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        ) as m_docx:
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="docx",
                cabecalho="Cabeçalho Teste",
            )
        assert isinstance(response, HttpResponse)
        m_docx.assert_called_once()

    def test_gerar_com_cabecalho_padrao(
        self,
        sumula_escolhas_service: Any,
        mock_cargos_response: Any,
        mock_candidatos_response: Any,
        mock_escolhas_response: Any,
    ) -> None:
        """Testa que usa cabeçalho padrão automaticamente quando preenchido."""
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response  # noqa: E501
        sumula_escolhas_service.context["cabecalho_padrao"] = (
            "Cabeçalho Padrão"
        )
        with patch(
            "relatorios.services.relatorios.sumula_escolhas.render",
            return_value=HttpResponse("OK"),
        ) as m_render:
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
                cabecalho="",
            )
        _, args, kwargs = m_render.mock_calls[0]
        context = args[2] if len(args) >= 3 else kwargs.get("context")
        assert context["cabecalho_padrao"] == "Cabeçalho Padrão"

    def test_gerar_filtra_escolhas_realizadas(
        self,
        sumula_escolhas_service: Any,
        mock_cargos_response: Any,
        mock_candidatos_response: Any,
        mock_escolhas_response: Any,
    ) -> None:
        """Testa que filtra apenas escolhas realizadas."""
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response  # noqa: E501
        with patch(
            "relatorios.services.relatorios.sumula_escolhas.render",
            return_value=HttpResponse("OK"),
        ):
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
            )
        assert isinstance(response, HttpResponse)
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.assert_called_once()
        call_args = sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.call_args  # noqa: E501
        assert call_args[1]["situacao"] is None

    def test_gerar_filtra_reconvocacao(
        self,
        sumula_escolhas_service: Any,
        mock_cargos_response: Any,
        mock_candidatos_response: Any,
    ) -> None:
        """Testa que filtra escolhas com situação reconvocacao."""
        escolhas = [
            {
                "candidato_uuid": "candidato-uuid-1",
                "situacao": "reconvocacao",
                "tipo_vaga": "definitiva",
                "vaga_escola": {
                    "escola": {
                        "nome_oficial": "EMEF Teste",
                        "codigo_eol": "12345",
                        "dre": {"codigo": "DRE001", "nome": "DRE Butantã"},
                    }
                },
            },
            {
                "candidato_uuid": "candidato-uuid-1",
                "situacao": "escolha",
                "tipo_vaga": "definitiva",
                "vaga_escola": {
                    "escola": {
                        "nome_oficial": "EMEF Teste 2",
                        "codigo_eol": "12346",
                        "dre": {"codigo": "DRE001", "nome": "DRE Butantã"},
                    }
                },
            },
        ]
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = escolhas  # noqa: E501
        with patch(
            "relatorios.services.relatorios.sumula_escolhas.render",
            return_value=HttpResponse("OK"),
        ):
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
            )
        assert isinstance(response, HttpResponse)

    def test_gerar_distribui_classificacao_por_categoria_efetiva(
        self, sumula_escolhas_service: Any, mock_cargos_response: Any
    ) -> None:
        """Testa distribuição das colunas de classificação por categoria."""
        candidatos_response = _MockResponse(
            {
                "results": [
                    {
                        "uuid": "candidato-geral",
                        "codigo_cargo": "123",
                        "descricao_cargo": "Professor de Educação Infantil",
                        "categoria_efetiva": "GERAL",
                        "classificacao": 11,
                        "classificacao_nna": 101,
                        "classificacao_pcd": 201,
                        "candidato": {"nome": "Candidato Geral"},
                    },
                    {
                        "uuid": "candidato-nna",
                        "codigo_cargo": "123",
                        "descricao_cargo": "Professor de Educação Infantil",
                        "categoria_efetiva": "NNA",
                        "classificacao": 12,
                        "classificacao_nna": 102,
                        "classificacao_pcd": 202,
                        "candidato": {"nome": "Candidato NNA"},
                    },
                    {
                        "uuid": "candidato-pcd",
                        "codigo_cargo": "123",
                        "descricao_cargo": "Professor de Educação Infantil",
                        "categoria_efetiva": "PCD",
                        "classificacao": 13,
                        "classificacao_nna": 103,
                        "classificacao_pcd": 203,
                        "candidato": {"nome": "Candidato PcD"},
                    },
                ]
            }
        )
        escolhas = [
            {
                "candidato_uuid": "candidato-geral",
                "situacao": "escolha",
                "tipo_vaga": "definitiva",
                "vaga_escola": {
                    "escola": {
                        "nome_oficial": "EMEF Teste",
                        "codigo_eol": "12345",
                        "dre": {"codigo": "DRE001", "nome": "DRE Butantã"},
                    }
                },
            },
            {
                "candidato_uuid": "candidato-nna",
                "situacao": "escolha",
                "tipo_vaga": "definitiva",
                "vaga_escola": {
                    "escola": {
                        "nome_oficial": "EMEF Teste",
                        "codigo_eol": "12345",
                        "dre": {"codigo": "DRE001", "nome": "DRE Butantã"},
                    }
                },
            },
            {
                "candidato_uuid": "candidato-pcd",
                "situacao": "escolha",
                "tipo_vaga": "definitiva",
                "vaga_escola": {
                    "escola": {
                        "nome_oficial": "EMEF Teste",
                        "codigo_eol": "12345",
                        "dre": {"codigo": "DRE001", "nome": "DRE Butantã"},
                    }
                },
            },
        ]
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = escolhas  # noqa: E501
        with patch(
            "relatorios.services.relatorios.sumula_escolhas.render",
            return_value=HttpResponse("OK"),
        ):
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
            )
        assert isinstance(response, HttpResponse)
        escolhas_resultado = dados[0]["dres"][0]["escolas"][0]["escolhas"]
        por_nome = {e["nome_candidato"]: e for e in escolhas_resultado}
        geral = por_nome["Candidato Geral"]
        assert geral["classificacao"] == 11
        assert geral["classificacao_nna"] == "-"
        assert geral["classificacao_pcd"] == "-"
        nna = por_nome["Candidato NNA"]
        assert nna["classificacao"] == 12
        assert nna["classificacao_nna"] == 102
        assert nna["classificacao_pcd"] == "-"
        pcd = por_nome["Candidato PcD"]
        assert pcd["classificacao"] == 13
        assert pcd["classificacao_nna"] == "-"
        assert pcd["classificacao_pcd"] == 203

    def test_gerar_filtra_situacao_none(
        self,
        sumula_escolhas_service: Any,
        mock_cargos_response: Any,
        mock_candidatos_response: Any,
    ) -> None:
        """Testa que filtra escolhas com situação None."""
        escolhas = [
            {
                "candidato_uuid": "candidato-uuid-1",
                "situacao": None,
                "tipo_vaga": "definitiva",
                "vaga_escola": {
                    "escola": {
                        "nome_oficial": "EMEF Teste",
                        "codigo_eol": "12345",
                        "dre": {"codigo": "DRE001", "nome": "DRE Butantã"},
                    }
                },
            }
        ]
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = escolhas  # noqa: E501
        with patch(
            "relatorios.services.relatorios.sumula_escolhas.render",
            return_value=HttpResponse("OK"),
        ):
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
            )
        assert isinstance(response, HttpResponse)

    def test_gerar_erro_buscar_candidatos(
        self, sumula_escolhas_service: Any, mock_cargos_response: Any
    ) -> None:
        """Testa que erro ao buscar candidatos é propagado."""
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.side_effect = Exception(  # noqa: E501
            "Erro API"
        )
        with pytest.raises(Exception, match="Erro API"):
            sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
            )

    def test_gerar_erro_buscar_escolhas(
        self,
        sumula_escolhas_service: Any,
        mock_cargos_response: Any,
        mock_candidatos_response: Any,
    ) -> None:
        """Testa que erro ao buscar escolhas é propagado."""
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = Exception(  # noqa: E501
            "Erro Escolhas"
        )
        with pytest.raises(Exception, match="Erro Escolhas"):
            sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
            )

    def test_gerar_escolha_sem_candidato_uuid(
        self,
        sumula_escolhas_service: Any,
        mock_cargos_response: Any,
        mock_candidatos_response: Any,
    ) -> None:
        """Testa que escolhas sem candidato_uuid são ignoradas."""
        escolhas = [
            {"candidato_uuid": None},
            {"candidato_uuid": "candidato-uuid-1"},
        ]
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = escolhas  # noqa: E501
        with patch(
            "relatorios.services.relatorios.sumula_escolhas.render",
            return_value=HttpResponse("OK"),
        ):
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
            )
        assert isinstance(response, HttpResponse)

    def test_gerar_candidato_nao_encontrado(
        self,
        sumula_escolhas_service: Any,
        mock_cargos_response: Any,
        mock_candidatos_response: Any,
    ) -> None:
        """Testa que escolhas com candidato não encontrado são ignoradas."""
        escolhas = [
            {
                "candidato_uuid": "candidato-inexistente",
                "situacao": "escolha",
                "tipo_vaga": "definitiva",
                "vaga_escola": {
                    "escola": {
                        "nome_oficial": "EMEF Teste",
                        "codigo_eol": "12345",
                        "dre": {"codigo": "DRE001", "nome": "DRE Butantã"},
                    }
                },
            }
        ]
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = escolhas  # noqa: E501
        with patch(
            "relatorios.services.relatorios.sumula_escolhas.render",
            return_value=HttpResponse("OK"),
        ):
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
            )
        assert isinstance(response, HttpResponse)

    def test_gerar_candidatos_lista_direta(
        self,
        sumula_escolhas_service: Any,
        mock_cargos_response: Any,
        mock_escolhas_response: Any,
    ) -> None:
        """Testa quando candidatos vem como lista direta (não dict com."""
        candidatos_lista = [
            {
                "uuid": "candidato-uuid-1",
                "codigo_cargo": "123",
                "classificacao": 1,
                "candidato": {"nome": "João", "rg": "123", "cpf": "123"},
            }
        ]
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = _MockResponse(  # noqa: E501
            candidatos_lista
        )
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response  # noqa: E501
        with patch(
            "relatorios.services.relatorios.sumula_escolhas.render",
            return_value=HttpResponse("OK"),
        ):
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
            )
        assert isinstance(response, HttpResponse)

    def test_gerar_formato_csv(
        self,
        sumula_escolhas_service: Any,
        mock_cargos_response: Any,
        mock_candidatos_response: Any,
        mock_escolhas_response: Any,
    ) -> None:
        """Testa geração com formato CSV (tratado como XLS)."""
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response  # noqa: E501
        with patch.object(
            sumula_escolhas_service,
            "render_to_xls",
            return_value=HttpResponse(
                b"xlsx",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        ) as m_xls:
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="csv",
            )
        assert isinstance(response, HttpResponse)
        m_xls.assert_called_once()

    def test_gerar_formato_doc(
        self,
        sumula_escolhas_service: Any,
        mock_cargos_response: Any,
        mock_candidatos_response: Any,
        mock_escolhas_response: Any,
    ) -> None:
        """Testa geração com formato DOC (tratado como DOCX)."""
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response  # noqa: E501
        with patch.object(
            sumula_escolhas_service,
            "render_to_docx",
            return_value=HttpResponse(
                b"docx",
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ),
        ) as m_docx:
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="doc",
            )
        assert isinstance(response, HttpResponse)
        m_docx.assert_called_once()

    def test_gerar_cargo_sem_descricao(
        self,
        sumula_escolhas_service: Any,
        mock_candidatos_response: Any,
        mock_escolhas_response: Any,
    ) -> None:
        """Testa quando candidato não tem descrição de cargo."""
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = _MockResponse(  # noqa: E501
            []
        )
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response  # noqa: E501
        with patch(
            "relatorios.services.relatorios.sumula_escolhas.render",
            return_value=HttpResponse("OK"),
        ):
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
            )
        assert isinstance(response, HttpResponse)

    def test_gerar_cargo_codigo_int(
        self,
        sumula_escolhas_service: Any,
        mock_candidatos_response: Any,
        mock_escolhas_response: Any,
    ) -> None:
        """Testa quando código do cargo é inteiro."""
        cargos_response = _MockResponse(
            [{"cargo_codigo": 123, "cargo_nome": "Professor"}]
        )
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response  # noqa: E501
        with patch(
            "relatorios.services.relatorios.sumula_escolhas.render",
            return_value=HttpResponse("OK"),
        ):
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
            )
        assert isinstance(response, HttpResponse)

    def test_gerar_erro_buscar_cargos_continua(
        self,
        sumula_escolhas_service: Any,
        mock_candidatos_response: Any,
        mock_escolhas_response: Any,
    ) -> None:
        """Testa que erro ao buscar cargos não interrompe o processo."""
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.side_effect = Exception(  # noqa: E501
            "Erro Cargos"
        )
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response  # noqa: E501
        with patch(
            "relatorios.services.relatorios.sumula_escolhas.render",
            return_value=HttpResponse("OK"),
        ):
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
            )
        assert isinstance(response, HttpResponse)

    def test_gerar_tipo_vaga_invalido(
        self,
        sumula_escolhas_service: Any,
        mock_cargos_response: Any,
        mock_candidatos_response: Any,
    ) -> None:
        """Testa quando tipo_vaga é inválido."""
        escolhas = [
            {
                "candidato_uuid": "candidato-uuid-1",
                "situacao": "escolha",
                "tipo_vaga": "invalido",
                "vaga_escola": {
                    "escola": {
                        "nome_oficial": "EMEF Teste",
                        "codigo_eol": "12345",
                        "dre": {"codigo": "DRE001", "nome": "DRE Butantã"},
                    }
                },
            }
        ]
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = escolhas  # noqa: E501
        with patch(
            "relatorios.services.relatorios.sumula_escolhas.render",
            return_value=HttpResponse("OK"),
        ):
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
            )
        assert isinstance(response, HttpResponse)

    def test_gerar_cargo_sem_descricao_com_codigo(
        self,
        sumula_escolhas_service: Any,
        mock_candidatos_response: Any,
        mock_escolhas_response: Any,
    ) -> None:
        """Testa quando candidato não tem descrição de cargo mas tem código."""
        candidatos_response = _MockResponse(
            {
                "results": [
                    {
                        "uuid": "candidato-uuid-1",
                        "codigo_cargo": "999",
                        "descricao_cargo": "",
                        "classificacao": 1,
                        "candidato": {
                            "nome": "João",
                            "rg": "123",
                            "cpf": "123",
                        },
                    }
                ]
            }
        )
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = _MockResponse(  # noqa: E501
            []
        )
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response  # noqa: E501
        with patch(
            "relatorios.services.relatorios.sumula_escolhas.render",
            return_value=HttpResponse("OK"),
        ):
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
            )
        assert isinstance(response, HttpResponse)
        assert len(dados) > 0
        if len(dados) > 0 and len(dados[0].get("dres", [])) > 0:
            escolas = dados[0]["dres"][0].get("escolas", [])
            if escolas and len(escolas) > 0:
                escolhas = escolas[0].get("escolhas", [])
                if escolhas:
                    pass

    def test_gerar_cargo_sem_descricao_sem_codigo(
        self, sumula_escolhas_service: Any, mock_escolhas_response: Any
    ) -> None:
        """Testa quando candidato não tem descrição nem código de cargo (linha."""
        candidatos_response = _MockResponse(
            {
                "results": [
                    {
                        "uuid": "candidato-uuid-1",
                        "codigo_cargo": "",
                        "descricao_cargo": "",
                        "classificacao": 1,
                        "candidato": {
                            "nome": "João",
                            "rg": "123",
                            "cpf": "123",
                        },
                    }
                ]
            }
        )
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = _MockResponse(  # noqa: E501
            []
        )
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response  # noqa: E501
        with patch(
            "relatorios.services.relatorios.sumula_escolhas.render",
            return_value=HttpResponse("OK"),
        ):
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
            )
        assert isinstance(response, HttpResponse)
        assert len(dados) > 0
        if len(dados) > 0:
            assert dados[0]["descricao"] == "Cargo não informado"

    def test_gerar_candidato_sem_candidato_obj(
        self,
        sumula_escolhas_service: Any,
        mock_cargos_response: Any,
        mock_escolhas_response: Any,
    ) -> None:
        """Testa quando candidato não tem objeto candidato."""
        candidatos_response = _MockResponse(
            {
                "results": [
                    {
                        "uuid": "candidato-uuid-1",
                        "codigo_cargo": "123",
                        "classificacao": 1,
                        "candidato": None,
                    }
                ]
            }
        )
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response  # noqa: E501
        with patch(
            "relatorios.services.relatorios.sumula_escolhas.render",
            return_value=HttpResponse("OK"),
        ):
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
            )
        assert isinstance(response, HttpResponse)


class TestAgruparPorCargoDreEEscola:
    """Testes para o método _agrupar_por_cargo_dre_e_escola."""

    def test_agrupar_por_cargo_dre_e_escola_basico(
        self, sumula_escolhas_service: Any
    ) -> None:
        """Testa agrupamento básico por cargo, DRE e escola."""
        escolhas = [
            {
                "cargo_codigo": "123",
                "cargo_descricao": "Professor",
                "dre_codigo": "DRE001",
                "dre_nome": "DRE Butantã",
                "escola_nome": "EMEF Teste",
                "escola_codigo_eol": "12345",
                "classificacao": 1,
                "nome_candidato": "João",
            },
            {
                "cargo_codigo": "123",
                "cargo_descricao": "Professor",
                "dre_codigo": "DRE001",
                "dre_nome": "DRE Butantã",
                "escola_nome": "EMEF Teste",
                "escola_codigo_eol": "12345",
                "classificacao": 2,
                "nome_candidato": "Maria",
            },
        ]
        resultado = sumula_escolhas_service._agrupar_por_cargo_dre_e_escola(
            escolhas
        )
        assert len(resultado) == 1
        assert resultado[0]["codigo"] == "123"
        assert resultado[0]["descricao"] == "Professor"
        assert len(resultado[0]["dres"]) == 1
        assert len(resultado[0]["dres"][0]["escolas"]) == 1
        assert len(resultado[0]["dres"][0]["escolas"][0]["escolhas"]) == 2

    def test_agrupar_por_cargo_dre_e_escola_ordenacao_candidatos(
        self, sumula_escolhas_service: Any
    ) -> None:
        """Testa que candidatos são ordenados por classificação."""
        escolhas = [
            {
                "cargo_codigo": "123",
                "cargo_descricao": "Professor",
                "dre_codigo": "DRE001",
                "dre_nome": "DRE Butantã",
                "escola_nome": "EMEF Teste",
                "escola_codigo_eol": "12345",
                "classificacao": 3,
                "nome_candidato": "Terceiro",
            },
            {
                "cargo_codigo": "123",
                "cargo_descricao": "Professor",
                "dre_codigo": "DRE001",
                "dre_nome": "DRE Butantã",
                "escola_nome": "EMEF Teste",
                "escola_codigo_eol": "12345",
                "classificacao": 1,
                "nome_candidato": "Primeiro",
            },
            {
                "cargo_codigo": "123",
                "cargo_descricao": "Professor",
                "dre_codigo": "DRE001",
                "dre_nome": "DRE Butantã",
                "escola_nome": "EMEF Teste",
                "escola_codigo_eol": "12345",
                "classificacao": 2,
                "nome_candidato": "Segundo",
            },
        ]
        resultado = sumula_escolhas_service._agrupar_por_cargo_dre_e_escola(
            escolhas
        )
        escolhas_ordenadas = resultado[0]["dres"][0]["escolas"][0]["escolhas"]
        assert escolhas_ordenadas[0]["classificacao"] == 1
        assert escolhas_ordenadas[1]["classificacao"] == 2
        assert escolhas_ordenadas[2]["classificacao"] == 3

    def test_agrupar_por_cargo_dre_e_escola_sem_descricao_cargo(
        self, sumula_escolhas_service: Any
    ) -> None:
        """Testa quando não há descrição do cargo."""
        escolhas = [
            {
                "cargo_codigo": "123",
                "cargo_descricao": "",
                "dre_codigo": "DRE001",
                "dre_nome": "DRE Butantã",
                "escola_nome": "EMEF Teste",
                "escola_codigo_eol": "12345",
                "classificacao": 1,
                "nome_candidato": "João",
            }
        ]
        resultado = sumula_escolhas_service._agrupar_por_cargo_dre_e_escola(
            escolhas
        )
        assert resultado[0]["descricao"] == "Cargo 123"

    def test_agrupar_por_cargo_dre_e_escola_sem_codigo_cargo(
        self, sumula_escolhas_service: Any
    ) -> None:
        """Testa quando não há código do cargo."""
        escolhas = [
            {
                "cargo_codigo": "",
                "cargo_descricao": "",
                "dre_codigo": "DRE001",
                "dre_nome": "DRE Butantã",
                "escola_nome": "EMEF Teste",
                "escola_codigo_eol": "12345",
                "classificacao": 1,
                "nome_candidato": "João",
            }
        ]
        resultado = sumula_escolhas_service._agrupar_por_cargo_dre_e_escola(
            escolhas
        )
        assert resultado[0]["descricao"] == "Cargo não informado"

    def test_agrupar_por_cargo_dre_e_escola_sem_dre_nome(
        self, sumula_escolhas_service: Any
    ) -> None:
        """Testa quando não há nome da DRE."""
        escolhas = [
            {
                "cargo_codigo": "123",
                "cargo_descricao": "Professor",
                "dre_codigo": "DRE001",
                "dre_nome": "",
                "escola_nome": "EMEF Teste",
                "escola_codigo_eol": "12345",
                "classificacao": 1,
                "nome_candidato": "João",
            }
        ]
        resultado = sumula_escolhas_service._agrupar_por_cargo_dre_e_escola(
            escolhas
        )
        assert resultado[0]["dres"][0]["nome"] == "DRE DRE001"

    def test_agrupar_por_cargo_dre_e_escola_sem_dre_codigo(
        self, sumula_escolhas_service: Any
    ) -> None:
        """Testa quando não há código da DRE."""
        escolhas = [
            {
                "cargo_codigo": "123",
                "cargo_descricao": "Professor",
                "dre_codigo": "",
                "dre_nome": "",
                "escola_nome": "EMEF Teste",
                "escola_codigo_eol": "12345",
                "classificacao": 1,
                "nome_candidato": "João",
            }
        ]
        resultado = sumula_escolhas_service._agrupar_por_cargo_dre_e_escola(
            escolhas
        )
        assert resultado[0]["dres"][0]["nome"] == "DRE não informada"

    def test_agrupar_por_cargo_dre_e_escola_sem_escola_nome(
        self, sumula_escolhas_service: Any
    ) -> None:
        """Testa quando não há nome da escola."""
        escolhas = [
            {
                "cargo_codigo": "123",
                "cargo_descricao": "Professor",
                "dre_codigo": "DRE001",
                "dre_nome": "DRE Butantã",
                "escola_nome": "",
                "escola_codigo_eol": "12345",
                "classificacao": 1,
                "nome_candidato": "João",
            }
        ]
        resultado = sumula_escolhas_service._agrupar_por_cargo_dre_e_escola(
            escolhas
        )
        assert (
            resultado[0]["dres"][0]["escolas"][0]["nome"] == "Escola EOL 12345"
        )

    def test_agrupar_por_cargo_dre_e_escola_sem_escola_codigo_eol(
        self, sumula_escolhas_service: Any
    ) -> None:
        """Testa quando não há código EOL da escola."""
        escolhas = [
            {
                "cargo_codigo": "123",
                "cargo_descricao": "Professor",
                "dre_codigo": "DRE001",
                "dre_nome": "DRE Butantã",
                "escola_nome": "",
                "escola_codigo_eol": "",
                "classificacao": 1,
                "nome_candidato": "João",
            }
        ]
        resultado = sumula_escolhas_service._agrupar_por_cargo_dre_e_escola(
            escolhas
        )
        assert (
            resultado[0]["dres"][0]["escolas"][0]["nome"]
            == "Unidade Escolar não informada"
        )

    def test_agrupar_por_cargo_dre_e_escola_ordenacao_escolas(
        self, sumula_escolhas_service: Any
    ) -> None:
        """Testa ordenação de escolas por nome."""
        escolhas = [
            {
                "cargo_codigo": "123",
                "cargo_descricao": "Professor",
                "dre_codigo": "DRE001",
                "dre_nome": "DRE Butantã",
                "escola_nome": "EMEF B",
                "escola_codigo_eol": "12346",
                "classificacao": 1,
                "nome_candidato": "João",
            },
            {
                "cargo_codigo": "123",
                "cargo_descricao": "Professor",
                "dre_codigo": "DRE001",
                "dre_nome": "DRE Butantã",
                "escola_nome": "EMEF A",
                "escola_codigo_eol": "12345",
                "classificacao": 1,
                "nome_candidato": "Maria",
            },
        ]
        resultado = sumula_escolhas_service._agrupar_por_cargo_dre_e_escola(
            escolhas
        )
        escolas = resultado[0]["dres"][0]["escolas"]
        assert escolas[0]["nome"] == "EMEF A"
        assert escolas[1]["nome"] == "EMEF B"

    def test_agrupar_por_cargo_dre_e_escola_ordenacao_dres(
        self, sumula_escolhas_service: Any
    ) -> None:
        """Testa ordenação de DREs por nome."""
        escolhas = [
            {
                "cargo_codigo": "123",
                "cargo_descricao": "Professor",
                "dre_codigo": "DRE002",
                "dre_nome": "DRE Centro",
                "escola_nome": "EMEF Teste",
                "escola_codigo_eol": "12345",
                "classificacao": 1,
                "nome_candidato": "João",
            },
            {
                "cargo_codigo": "123",
                "cargo_descricao": "Professor",
                "dre_codigo": "DRE001",
                "dre_nome": "DRE Butantã",
                "escola_nome": "EMEF Teste 2",
                "escola_codigo_eol": "12346",
                "classificacao": 1,
                "nome_candidato": "Maria",
            },
        ]
        resultado = sumula_escolhas_service._agrupar_por_cargo_dre_e_escola(
            escolhas
        )
        dres = resultado[0]["dres"]
        assert dres[0]["nome"] == "DRE Butantã"
        assert dres[1]["nome"] == "DRE Centro"

    def test_agrupar_por_cargo_dre_e_escola_ordenacao_cargos(
        self, sumula_escolhas_service: Any
    ) -> None:
        """Testa ordenação de cargos por descrição."""
        escolhas = [
            {
                "cargo_codigo": "456",
                "cargo_descricao": "Professor B",
                "dre_codigo": "DRE001",
                "dre_nome": "DRE Butantã",
                "escola_nome": "EMEF Teste",
                "escola_codigo_eol": "12345",
                "classificacao": 1,
                "nome_candidato": "João",
            },
            {
                "cargo_codigo": "123",
                "cargo_descricao": "Professor A",
                "dre_codigo": "DRE001",
                "dre_nome": "DRE Butantã",
                "escola_nome": "EMEF Teste 2",
                "escola_codigo_eol": "12346",
                "classificacao": 1,
                "nome_candidato": "Maria",
            },
        ]
        resultado = sumula_escolhas_service._agrupar_por_cargo_dre_e_escola(
            escolhas
        )
        assert resultado[0]["descricao"] == "Professor A"
        assert resultado[1]["descricao"] == "Professor B"

    def test_agrupar_por_cargo_dre_e_escola_classificacao_nao_numerica(
        self, sumula_escolhas_service: Any
    ) -> None:
        """Testa ordenação quando classificação não é numérica."""
        escolhas = [
            {
                "cargo_codigo": "123",
                "cargo_descricao": "Professor",
                "dre_codigo": "DRE001",
                "dre_nome": "DRE Butantã",
                "escola_nome": "EMEF Teste",
                "escola_codigo_eol": "12345",
                "classificacao": "-",
                "nome_candidato": "João",
            },
            {
                "cargo_codigo": "123",
                "cargo_descricao": "Professor",
                "dre_codigo": "DRE001",
                "dre_nome": "DRE Butantã",
                "escola_nome": "EMEF Teste",
                "escola_codigo_eol": "12345",
                "classificacao": 1,
                "nome_candidato": "Maria",
            },
        ]
        resultado = sumula_escolhas_service._agrupar_por_cargo_dre_e_escola(
            escolhas
        )
        escolhas_ordenadas = resultado[0]["dres"][0]["escolas"][0]["escolhas"]
        assert escolhas_ordenadas[0]["classificacao"] == 1
        assert escolhas_ordenadas[1]["classificacao"] == "-"


class TestRenderToXls:
    """Testes para o método render_to_xls."""

    def test_render_to_xls_success(self, sumula_escolhas_service: Any) -> None:
        """Testa geração de Excel com sucesso."""
        cargos_list = [
            {
                "descricao": "Professor",
                "dres": [
                    {
                        "nome": "DRE Butantã",
                        "escolas": [
                            {
                                "nome": "EMEF Teste",
                                "escolhas": [
                                    {
                                        "classificacao": 1,
                                        "nome_candidato": "João",
                                        "tipo_vaga": "D",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
        context = sumula_escolhas_service.context.copy()
        context["cargos"] = cargos_list
        context["cabecalho"] = "Cabeçalho Teste"
        response = sumula_escolhas_service.render_to_xls(
            context=context, filename="test.xlsx"
        )
        assert isinstance(response, HttpResponse)
        assert (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            in response["Content-Type"]
        )
        assert "attachment" in response["Content-Disposition"]
        assert "test.xlsx" in response["Content-Disposition"]

    def test_render_to_xls_sem_cabecalho(
        self, sumula_escolhas_service: Any
    ) -> None:
        """Testa geração de Excel sem cabeçalho."""
        cargos_list = [{"descricao": "Professor", "dres": []}]
        context = sumula_escolhas_service.context.copy()
        context["cargos"] = cargos_list
        context["cabecalho"] = ""
        response = sumula_escolhas_service.render_to_xls(
            context=context, filename="test.xlsx"
        )
        assert isinstance(response, HttpResponse)

    def test_render_to_xls_multiplos_cargos_dres_escolas(
        self, sumula_escolhas_service: Any
    ) -> None:
        """Testa geração de Excel com múltiplos cargos, DREs e escolas."""
        cargos_list = [
            {
                "descricao": "Professor A",
                "dres": [
                    {
                        "nome": "DRE 1",
                        "escolas": [
                            {
                                "nome": "EMEF A",
                                "escolhas": [
                                    {
                                        "classificacao": 1,
                                        "nome_candidato": "João",
                                        "tipo_vaga": "D",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
            {
                "descricao": "Professor B",
                "dres": [
                    {
                        "nome": "DRE 2",
                        "escolas": [
                            {
                                "nome": "EMEF B",
                                "escolhas": [
                                    {
                                        "classificacao": 1,
                                        "nome_candidato": "Maria",
                                        "tipo_vaga": "P",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
        ]
        context = sumula_escolhas_service.context.copy()
        context["cargos"] = cargos_list
        context["cabecalho"] = "Cabeçalho"
        response = sumula_escolhas_service.render_to_xls(
            context=context, filename="test.xlsx"
        )
        assert isinstance(response, HttpResponse)

    @patch(
        "relatorios.services.relatorios.sumula_escolhas.OPENPYXL_AVAILABLE",
        False,
    )
    def test_render_to_xls_openpyxl_nao_disponivel(
        self, sumula_escolhas_service: Any
    ) -> None:
        """Testa erro quando openpyxl não está disponível."""
        cargos_list = []  # type: ignore[var-annotated]
        context = sumula_escolhas_service.context.copy()
        context["cargos"] = cargos_list
        context["cabecalho"] = "Cabeçalho"
        with pytest.raises(ImportError, match="openpyxl"):
            sumula_escolhas_service.render_to_xls(
                context=context, filename="test.xlsx"
            )

    def test_render_to_xls_exception(
        self, sumula_escolhas_service: Any
    ) -> None:
        """Testa tratamento de exceção no render_to_xls."""
        cargos_list = []  # type: ignore[var-annotated]
        context = sumula_escolhas_service.context.copy()
        context["cargos"] = cargos_list
        context["cabecalho"] = "Cabeçalho"
        with (
            patch(
                "relatorios.services.relatorios.sumula_escolhas.Workbook",
                side_effect=Exception("Erro Excel"),
            ),
            pytest.raises(Exception, match="Erro Excel"),
        ):
            sumula_escolhas_service.render_to_xls(
                context=context, filename="test.xlsx"
            )


class TestRenderToDocx:
    """Testes para o método render_to_docx."""

    @patch(
        "relatorios.services.relatorios.sumula_escolhas.DOCX_AVAILABLE", False
    )
    def test_render_to_docx_python_docx_nao_disponivel(
        self, sumula_escolhas_service: Any
    ) -> None:
        """Testa erro quando python-docx não está disponível."""
        cargos_list = []  # type: ignore[var-annotated]
        with pytest.raises(ImportError, match="python-docx"):
            sumula_escolhas_service.render_to_docx(
                cargos_list, "Cabeçalho", "test.docx"
            )

    @patch(
        "relatorios.services.relatorios.sumula_escolhas.DOCX_AVAILABLE", True
    )
    @patch(
        "relatorios.services.relatorios.sumula_escolhas.Document", create=True
    )
    @patch(
        "relatorios.services.relatorios.sumula_escolhas.Inches", create=True
    )
    @patch("relatorios.services.relatorios.sumula_escolhas.Pt", create=True)
    @patch(
        "relatorios.services.relatorios.sumula_escolhas.RGBColor", create=True
    )
    @patch(
        "relatorios.services.relatorios.sumula_escolhas.WD_ALIGN_PARAGRAPH",
        create=True,
    )
    @patch("relatorios.services.relatorios.sumula_escolhas.qn", create=True)
    @patch(
        "relatorios.services.relatorios.sumula_escolhas.OxmlElement",
        create=True,
    )
    @patch("relatorios.services.relatorios.sumula_escolhas.BytesIO")
    def test_render_to_docx_completo_com_cabecalho(
        self,
        mock_bytesio: Any,
        mock_oxml_element: Any,
        mock_qn: Any,
        mock_wd_align: Any,
        mock_rgb_color: Any,
        mock_pt: Any,
        mock_inches: Any,
        mock_document: Any,
        sumula_escolhas_service: Any,
    ) -> None:
        """Testa geração completa de Word com cabeçalho e dados."""
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        mock_section = MagicMock()
        mock_doc.sections = [mock_section]
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_paragraph.add_run.return_value = mock_run
        mock_paragraph._element = MagicMock()
        mock_paragraph._element.get_or_add_pPr.return_value = MagicMock()
        mock_paragraph._element.get_or_add_pPr.return_value.find.return_value = None  # noqa: E501
        mock_doc.add_paragraph.return_value = mock_paragraph
        mock_table = MagicMock()
        mock_header_row = MagicMock()
        mock_header_cells = []
        for _i in range(5):
            mock_cell = MagicMock()
            mock_cell.paragraphs = [MagicMock()]
            mock_cell.paragraphs[0].runs = [MagicMock()]
            mock_cell._element = MagicMock()
            mock_cell._element.get_or_add_tcPr.return_value = MagicMock()
            mock_cell._element.get_or_add_tcPr.return_value.find.return_value = None  # noqa: E501
            mock_header_cells.append(mock_cell)
        mock_header_row.cells = mock_header_cells
        mock_table.rows = [mock_header_row]
        mock_data_row = MagicMock()
        mock_data_cells = []
        for _i in range(5):
            mock_cell = MagicMock()
            mock_cell.paragraphs = [MagicMock()]
            mock_cell.paragraphs[0].runs = [MagicMock()]
            mock_data_cells.append(mock_cell)
        mock_data_row.cells = mock_data_cells
        mock_table.add_row.return_value = mock_data_row
        mock_doc.add_table.return_value = mock_table
        mock_buffer = MagicMock()
        mock_buffer.read.return_value = b"docx content"
        mock_bytesio.return_value = mock_buffer
        mock_inches.return_value = MagicMock()
        mock_pt.return_value = MagicMock()
        mock_rgb_color.return_value = MagicMock()
        mock_wd_align.CENTER = "CENTER"
        mock_wd_align.LEFT = "LEFT"
        mock_qn.return_value = "w:shd"
        mock_oxml_element.return_value = MagicMock()
        cargos_list = [
            {
                "descricao": "Professor de Educação Infantil",
                "dres": [
                    {
                        "nome": "DRE Butantã",
                        "escolas": [
                            {
                                "nome": "EMEF Teste",
                                "escolhas": [
                                    {
                                        "classificacao": 1,
                                        "nome_candidato": "João Silva",
                                        "tipo_vaga": "D",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
        response = sumula_escolhas_service.render_to_docx(
            cargos_list, "<b>Cabeçalho Teste</b>", "test.docx"
        )
        assert isinstance(response, HttpResponse)
        assert (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            in response["Content-Type"]
        )
        assert "attachment" in response["Content-Disposition"]
        assert (
            "test.docx" in response["Content-Disposition"]
            or "relatorio_sumula_escolhas.docx"
            in response["Content-Disposition"]
        )
        mock_document.assert_called_once()
        mock_doc.save.assert_called_once_with(mock_buffer)

    @patch(
        "relatorios.services.relatorios.sumula_escolhas.DOCX_AVAILABLE", True
    )
    @patch(
        "relatorios.services.relatorios.sumula_escolhas.Document", create=True
    )
    @patch(
        "relatorios.services.relatorios.sumula_escolhas.Inches", create=True
    )
    @patch("relatorios.services.relatorios.sumula_escolhas.Pt", create=True)
    @patch(
        "relatorios.services.relatorios.sumula_escolhas.RGBColor", create=True
    )
    @patch(
        "relatorios.services.relatorios.sumula_escolhas.WD_ALIGN_PARAGRAPH",
        create=True,
    )
    @patch("relatorios.services.relatorios.sumula_escolhas.qn", create=True)
    @patch(
        "relatorios.services.relatorios.sumula_escolhas.OxmlElement",
        create=True,
    )
    @patch("relatorios.services.relatorios.sumula_escolhas.BytesIO")
    def test_render_to_docx_sem_cabecalho(
        self,
        mock_bytesio: Any,
        mock_oxml_element: Any,
        mock_qn: Any,
        mock_wd_align: Any,
        mock_rgb_color: Any,
        mock_pt: Any,
        mock_inches: Any,
        mock_document: Any,
        sumula_escolhas_service: Any,
    ) -> None:
        """Testa geração de Word sem cabeçalho."""
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        mock_section = MagicMock()
        mock_doc.sections = [mock_section]
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_paragraph.add_run.return_value = mock_run
        mock_paragraph._element = MagicMock()
        mock_paragraph._element.get_or_add_pPr.return_value = MagicMock()
        mock_paragraph._element.get_or_add_pPr.return_value.find.return_value = None  # noqa: E501
        mock_doc.add_paragraph.return_value = mock_paragraph
        mock_table = MagicMock()
        mock_table.rows = [MagicMock()]
        mock_table.rows[0].cells = [MagicMock() for _ in range(5)]
        for cell in mock_table.rows[0].cells:
            cell.paragraphs = [MagicMock()]
            cell.paragraphs[0].runs = [MagicMock()]
            cell._element = MagicMock()
            cell._element.get_or_add_tcPr.return_value = MagicMock()
            cell._element.get_or_add_tcPr.return_value.find.return_value = None
        mock_table.add_row.return_value = MagicMock()
        mock_table.add_row.return_value.cells = [MagicMock() for _ in range(5)]
        for cell in mock_table.add_row.return_value.cells:
            cell.paragraphs = [MagicMock()]
            cell.paragraphs[0].runs = [MagicMock()]
        mock_doc.add_table.return_value = mock_table
        mock_buffer = MagicMock()
        mock_buffer.read.return_value = b"docx content"
        mock_bytesio.return_value = mock_buffer
        mock_inches.return_value = MagicMock()
        mock_pt.return_value = MagicMock()
        mock_rgb_color.return_value = MagicMock()
        mock_wd_align.CENTER = "CENTER"
        mock_wd_align.LEFT = "LEFT"
        mock_qn.return_value = "w:shd"
        mock_oxml_element.return_value = MagicMock()
        cargos_list = [{"descricao": "Professor", "dres": []}]
        response = sumula_escolhas_service.render_to_docx(
            cargos_list, "", "test.docx"
        )
        assert isinstance(response, HttpResponse)

    @patch(
        "relatorios.services.relatorios.sumula_escolhas.DOCX_AVAILABLE", True
    )
    @patch(
        "relatorios.services.relatorios.sumula_escolhas.Document", create=True
    )
    @patch(
        "relatorios.services.relatorios.sumula_escolhas.Inches", create=True
    )
    @patch("relatorios.services.relatorios.sumula_escolhas.Pt", create=True)
    @patch(
        "relatorios.services.relatorios.sumula_escolhas.RGBColor", create=True
    )
    @patch(
        "relatorios.services.relatorios.sumula_escolhas.WD_ALIGN_PARAGRAPH",
        create=True,
    )
    @patch("relatorios.services.relatorios.sumula_escolhas.qn", create=True)
    @patch(
        "relatorios.services.relatorios.sumula_escolhas.OxmlElement",
        create=True,
    )
    @patch("relatorios.services.relatorios.sumula_escolhas.BytesIO")
    def test_render_to_docx_com_existing_shd(
        self,
        mock_bytesio: Any,
        mock_oxml_element: Any,
        mock_qn: Any,
        mock_wd_align: Any,
        mock_rgb_color: Any,
        mock_pt: Any,
        mock_inches: Any,
        mock_document: Any,
        sumula_escolhas_service: Any,
    ) -> None:
        """Testa quando já existe shading element (existing_shd)."""
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        mock_section = MagicMock()
        mock_doc.sections = [mock_section]
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_paragraph.add_run.return_value = mock_run
        mock_paragraph._element = MagicMock()
        mock_p_pr = MagicMock()
        mock_existing_shd = MagicMock()
        mock_p_pr.find.return_value = mock_existing_shd
        mock_paragraph._element.get_or_add_pPr.return_value = mock_p_pr
        mock_doc.add_paragraph.return_value = mock_paragraph
        mock_table = MagicMock()
        mock_table.rows = [MagicMock()]
        mock_table.rows[0].cells = [MagicMock() for _ in range(5)]
        for cell in mock_table.rows[0].cells:
            cell.paragraphs = [MagicMock()]
            cell.paragraphs[0].runs = [MagicMock()]
            cell._element = MagicMock()
            mock_tc_pr = MagicMock()
            mock_existing_shd_cell = MagicMock()
            mock_tc_pr.find.return_value = mock_existing_shd_cell
            cell._element.get_or_add_tcPr.return_value = mock_tc_pr
        mock_table.add_row.return_value = MagicMock()
        mock_table.add_row.return_value.cells = [MagicMock() for _ in range(5)]
        for cell in mock_table.add_row.return_value.cells:
            cell.paragraphs = [MagicMock()]
            cell.paragraphs[0].runs = [MagicMock()]
        mock_doc.add_table.return_value = mock_table
        mock_buffer = MagicMock()
        mock_buffer.read.return_value = b"docx content"
        mock_bytesio.return_value = mock_buffer
        mock_inches.return_value = MagicMock()
        mock_pt.return_value = MagicMock()
        mock_rgb_color.return_value = MagicMock()
        mock_wd_align.CENTER = "CENTER"
        mock_wd_align.LEFT = "LEFT"
        mock_qn.return_value = "w:shd"
        mock_oxml_element.return_value = MagicMock()
        cargos_list = [
            {
                "descricao": "Professor",
                "dres": [
                    {
                        "nome": "DRE Butantã",
                        "escolas": [
                            {
                                "nome": "EMEF Teste",
                                "escolhas": [
                                    {
                                        "classificacao": 1,
                                        "nome_candidato": "João",
                                        "tipo_vaga": "D",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
        response = sumula_escolhas_service.render_to_docx(
            cargos_list, "Cabeçalho", "test.docx"
        )
        assert isinstance(response, HttpResponse)
        assert mock_p_pr.remove.called

    @patch(
        "relatorios.services.relatorios.sumula_escolhas.DOCX_AVAILABLE", True
    )
    @patch("relatorios.services.relatorios.sumula_escolhas.Document")
    def test_render_to_docx_exception(
        self, mock_document: Any, sumula_escolhas_service: Any
    ) -> None:
        """Testa tratamento de exceção no render_to_docx."""
        mock_document.side_effect = Exception("Erro ao criar documento")
        cargos_list = []  # type: ignore[var-annotated]
        with pytest.raises(Exception, match="Erro ao criar documento"):
            sumula_escolhas_service.render_to_docx(
                cargos_list, "Cabeçalho", "test.docx"
            )


class TestIntegracaoCompleta:
    """Testes de integração completos."""

    def test_fluxo_completo_html(
        self,
        sumula_escolhas_service: Any,
        mock_cargos_response: Any,
        mock_candidatos_response: Any,
        mock_escolhas_response: Any,
    ) -> None:
        """Testa fluxo completo de geração HTML."""
        sumula_escolhas_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response  # noqa: E501
        sumula_escolhas_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response  # noqa: E501
        sumula_escolhas_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response  # noqa: E501
        with patch(
            "relatorios.services.relatorios.sumula_escolhas.render",
            return_value=HttpResponse("OK"),
        ) as m_render:
            response, dados = sumula_escolhas_service.gerar(
                processo_uuid="proc-123",
                request=_make_request(),
                formato="html",
                cabecalho="Teste",
            )
        assert isinstance(response, HttpResponse)
        m_render.assert_called_once()
        assert isinstance(dados, list)
        if len(dados) > 0:
            assert "codigo" in dados[0]
            assert "descricao" in dados[0]
            assert "dres" in dados[0]
