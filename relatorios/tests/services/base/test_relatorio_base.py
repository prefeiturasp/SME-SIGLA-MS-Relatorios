"""Módulo tests/services/base/test_relatorio_base."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock, patch

import pytest
from django.http import HttpResponse

from relatorios.models import ConfiguracaoRelatorio, Parametrizacao
from relatorios.services.base.relatorio_base import RelatorioBase

pytestmark = pytest.mark.django_db


@pytest.fixture
def configuracao_relatorio() -> Any:
    """Fixture que cria uma ConfiguracaoRelatorio para testes."""
    return ConfiguracaoRelatorio.objects.get_or_create(
        tipo="LAUDA_VAGAS",
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


class DummyRelatorio(RelatorioBase):
    """Define DummyRelatorio."""

    def gerar(
        self,
        processo_uuid: str,
        request: Any,
        formato: str = "html",
        cabecalho: str = "",
    ) -> Any:  # type: ignore[override]
        """Executa gerar."""
        return (HttpResponse("ok"), {})


def test_context_cabecalho_usa_gabarito_quando_cabecalho_vazio(
    configuracao_relatorio: Any, parametrizacao: Any
) -> None:
    """Verifica context cabecalho usa gabarito quando cabecalho vazio."""
    configuracao_relatorio.cabecalho = ""
    configuracao_relatorio.cabecalho_gabarito = "Gabarito Teste"
    configuracao_relatorio.save()
    rel = DummyRelatorio(
        configuracao=configuracao_relatorio, parametrizacao=parametrizacao
    )
    assert rel.context["cabecalho"] == "Gabarito Teste"


def test_context_cabecalho_prefere_cabecalho_sobre_gabarito(
    configuracao_relatorio: Any, parametrizacao: Any
) -> None:
    """Verifica context cabecalho prefere cabecalho sobre gabarito."""
    configuracao_relatorio.cabecalho = "Cabeçalho Customizado"
    configuracao_relatorio.cabecalho_gabarito = "Gabarito Teste"
    configuracao_relatorio.save()
    rel = DummyRelatorio(
        configuracao=configuracao_relatorio, parametrizacao=parametrizacao
    )
    assert rel.context["cabecalho"] == "Cabeçalho Customizado"


def test_context_cabecalho_vazio_quando_ambos_vazios(
    configuracao_relatorio: Any, parametrizacao: Any
) -> None:
    """Verifica context cabecalho vazio quando ambos vazios."""
    configuracao_relatorio.cabecalho = ""
    configuracao_relatorio.cabecalho_gabarito = ""
    configuracao_relatorio.save()
    rel = DummyRelatorio(
        configuracao=configuracao_relatorio, parametrizacao=parametrizacao
    )
    assert rel.context["cabecalho"] == "" or rel.context["cabecalho"] is None


def test_render_to_pdf_success(
    monkeypatch: Any, configuracao_relatorio: Any, parametrizacao: Any
) -> None:
    """Verifica render to pdf success."""
    rel = DummyRelatorio(
        configuracao=configuracao_relatorio, parametrizacao=parametrizacao
    )
    with (
        patch(
            "relatorios.services.base.relatorio_base.render_to_string",
            return_value="<html><body>PDF</body></html>",
        ) as m_render,
        patch("relatorios.services.base.relatorio_base.HTML") as m_html_cls,
    ):
        m_html = Mock()
        m_html_cls.return_value = m_html
        response = rel.render_to_pdf("tpl.html", {"x": 1}, filename="file.pdf")
    m_render.assert_called_once_with("tpl.html", {"x": 1})
    m_html_cls.assert_called_once()
    assert m_html.write_pdf.call_count == 1
    assert isinstance(response, HttpResponse)
    assert response["Content-Type"] == "application/pdf"
    assert 'attachment; filename="file.pdf"' in response["Content-Disposition"]


def test_render_to_pdf_error_propagates(
    monkeypatch: Any, configuracao_relatorio: Any, parametrizacao: Any
) -> None:
    """Verifica render to pdf error propagates."""
    rel = DummyRelatorio(
        configuracao=configuracao_relatorio, parametrizacao=parametrizacao
    )
    with (
        patch(
            "relatorios.services.base.relatorio_base.render_to_string",
            return_value="<html/>",
        ),
        patch("relatorios.services.base.relatorio_base.HTML") as m_html_cls,
    ):
        m_html = Mock()
        m_html.write_pdf.side_effect = RuntimeError("fail")
        m_html_cls.return_value = m_html
        with pytest.raises(RuntimeError):
            rel.render_to_pdf("x.html", {})


@pytest.mark.parametrize(
    "html,expected",
    [
        ("", ""),
        (None, ""),
        (
            "<p>Oi&nbsp;Mundo</p><br><p>Segunda&nbsp;&amp; Linha</p>",
            "Oi Mundo\n\nSegunda & Linha",
        ),
        ("Texto sem tags", "Texto sem tags"),
        ("<p>Um</p><p>Dois</p><p>Três</p>", "Um\nDois\nTrês"),
        ("A&nbsp;&lt;B&gt; &quot;C&quot; &#39;D&#39;", "A <B> \"C\" 'D'"),
        ("Linha1<br/><br />\n<br> Linha2", "Linha1\n\n Linha2"),
    ],
)
def test_processar_cabecalho_html(html: Any, expected: Any) -> None:
    """Verifica processar cabecalho html."""
    result = RelatorioBase.processar_cabecalho_html(html)
    assert result == expected.strip()
