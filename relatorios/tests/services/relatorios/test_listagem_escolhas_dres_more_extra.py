"""Módulo tests/services/relatorios/test_listagem_escolhas_dres_more_extra."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from django.http import HttpResponse

from relatorios.models import ConfiguracaoRelatorio, Parametrizacao
from relatorios.services.relatorios.listagem_escolhas_dres import (
    ListagemEscolhasDres,
)

pytestmark = pytest.mark.django_db


class _ImgResp:
    """Define _ImgResp."""

    content = b"fake-png"

    def raise_for_status(self) -> Any:
        """Executa raise for status."""
        return None


@pytest.fixture
def svc() -> Any:
    """Executa svc."""
    cfg = ConfiguracaoRelatorio.objects.get_or_create(
        tipo="LISTAGEM_ESCOLHAS_DRES"
    )[0]
    par = Parametrizacao.objects.get_or_create(cabecalho="Cabecalho Padrao")[0]
    return ListagemEscolhasDres(configuracao=cfg, parametrizacao=par)


def test_render_to_xls_with_logo_headers_and_footer(svc: Any) -> None:
    """Verifica render to xls with logo headers and footer."""
    svc.context["cabecalho"] = "CAB"
    escolhas = [
        {
            "cargo": "Professor",
            "classificacao": 1,
            "classificacao_deficiente": "-",
            "classificacao_nna": 2,
            "rf": "123",
            "rg": "999",
            "cpf": "111",
            "inscricao": "I1",
            "nome": "Ana",
            "telefone": "9999",
            "dre": "DRE 1",
            "codigo_eol": "100",
            "tipo_ue": "EMEF",
            "unidade": "UE 1",
            "tipo_vaga": "D",
        },
        {
            "cargo": "Professor",
            "classificacao": 2,
            "classificacao_deficiente": "-",
            "classificacao_nna": 3,
            "rf": "124",
            "rg": "998",
            "cpf": "222",
            "inscricao": "I2",
            "nome": "Beto",
            "telefone": "8888",
            "dre": "DRE 2",
            "codigo_eol": "200",
            "tipo_ue": "CEI",
            "unidade": "UE 2",
            "tipo_vaga": "P",
        },
    ]
    context = {
        "escolhas": escolhas,
        "usar_logotipo": True,
        "logo_url": "http://example/logo.png",
        "texto_final": "Rodape final",
    }
    with patch(
        "relatorios.services.relatorios.listagem_escolhas_dres.requests.get",
        return_value=_ImgResp(),
    ):
        response = svc.render_to_xls(
            context=context, filename="listagem-extra.xlsx"
        )
    assert isinstance(response, HttpResponse)
    assert response.status_code == 200
    assert "listagem-extra.xlsx" in response["Content-Disposition"]
