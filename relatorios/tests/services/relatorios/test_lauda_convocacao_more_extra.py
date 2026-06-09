"""Módulo tests/services/relatorios/test_lauda_convocacao_more_extra."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock, patch

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from relatorios.models import ConfiguracaoRelatorio, Parametrizacao
from relatorios.services.relatorios.lauda_convocacao import LaudaConvocacao

pytestmark = pytest.mark.django_db


class _Resp:
    """Define _Resp."""

    def __init__(self, content: Any = b"img") -> None:
        """Executa   init  ."""
        self.content = content

    def raise_for_status(self) -> Any:
        """Executa raise for status."""
        return None


@pytest.fixture
def svc(settings: Any) -> Any:
    """Executa svc."""
    settings.CANDIDATOS_API_URL = "http://candidatos"
    settings.CONVOCACAO_API_URL = "http://convocacao"
    settings.AGENDAS_API_URL = "http://agendas"
    cfg = ConfiguracaoRelatorio.objects.get_or_create(tipo="LAUDA_CONVOCACAO")[
        0
    ]
    par = Parametrizacao.objects.get_or_create(cabecalho="Cab Padrao")[0]
    return LaudaConvocacao(configuracao=cfg, parametrizacao=par)


def _cargos() -> Any:
    """Executa  cargos."""
    return [
        {
            "cargo_nome": "Professor",
            "sessoes": [
                {
                    "numero_sessao": 1,
                    "horario_formatado": "08:00 às 10:00",
                    "candidatos": [
                        {
                            "ordem_escolha": 1,
                            "codigo_inscricao": "INS1",
                            "classificacao": 1,
                            "classificacao_pcd": None,
                            "classificacao_nna": 2,
                            "candidato": {"nome": "Ana"},
                        }
                    ],
                }
            ],
        }
    ]


def test_renderers_xls_docx_with_logo_and_text(svc: Any) -> None:
    """Verifica renderers xls docx with logo and text."""
    svc.context.update(
        {
            "usar_logotipo": True,
            "logo_url": "http://img/logo.png",
            "texto_final": "Rodape",
        }
    )
    with patch(
        "relatorios.services.relatorios.lauda_convocacao.requests.get",
        return_value=_Resp(),
    ):
        xls = svc._render_xls(
            _cargos(), context=svc.context, filename="conv-extra.xlsx"
        )
    docx = svc.render_to_docx(
        _cargos(), svc.context, "Rodape", filename="conv-extra.docx"
    )
    assert isinstance(xls, HttpResponse)
    assert isinstance(docx, HttpResponse)
    assert "conv-extra.xlsx" in xls["Content-Disposition"]
    assert "conv-extra.docx" in docx["Content-Disposition"]


def test_render_xls_logo_error_path(svc: Any) -> None:
    """Verifica render xls logo error path."""
    svc.context.update(
        {"usar_logotipo": True, "logo_url": "http://img/logo.png"}
    )
    with patch(
        "relatorios.services.relatorios.lauda_convocacao.requests.get",
        side_effect=RuntimeError("img err"),
    ):
        xls = svc._render_xls(
            _cargos(), context=svc.context, filename="conv-logo-err.xlsx"
        )
    assert isinstance(xls, HttpResponse)


def test_gerar_doc_and_xls_routes(svc: Any) -> None:
    """Verifica gerar doc and xls routes."""
    req = RequestFactory().get("/x")
    svc.lauda_service = Mock()
    svc.lauda_service.processar_lauda_convocacao.return_value = {
        "cargos": _cargos()
    }
    with patch.object(
        svc, "render_to_docx", return_value=HttpResponse("docx")
    ):
        resp_docx, _ = svc.gerar("p1", req, formato="docx")
        assert resp_docx.status_code == 200
    with patch.object(svc, "_render_xls", return_value=HttpResponse("xls")):
        resp_xls, _ = svc.gerar("p1", req, formato="xls")
        assert resp_xls.status_code == 200
