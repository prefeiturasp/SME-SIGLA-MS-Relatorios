"""Módulo tests/services/test_factory_and_utils_extra."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from relatorios.models import ConfiguracaoRelatorio, Parametrizacao
from relatorios.services.base.utils import ajustar_logo_caminho
from relatorios.services.factory.relatorio_factory import RelatorioFactory

pytestmark = pytest.mark.django_db


def test_ajustar_logo_caminho_local_returns_same(settings: Any) -> None:
    """Verifica ajustar logo caminho local returns same."""
    settings.DJANGO_ENVIRONMENT = "local"
    settings.MS_PATH = "/ms-relatorios"
    assert ajustar_logo_caminho("/media/logo.png") == "/media/logo.png"


def test_ajustar_logo_caminho_non_local_prefixes_once(settings: Any) -> None:
    """Verifica ajustar logo caminho non local prefixes once."""
    settings.DJANGO_ENVIRONMENT = "hom"
    settings.MS_PATH = "/ms-relatorios"
    assert (
        ajustar_logo_caminho("/media/logo.png")
        == "/ms-relatorios/media/logo.png"
    )
    assert (
        ajustar_logo_caminho("/ms-relatorios/media/logo.png")
        == "/ms-relatorios/media/logo.png"
    )


def test_ajustar_logo_caminho_invalid_values_return_none() -> None:
    """Verifica ajustar logo caminho invalid values return none."""
    assert ajustar_logo_caminho(None) is None
    assert ajustar_logo_caminho(123) is None


def test_relatorio_factory_invalid_type_raises_value_error() -> None:
    """Verifica relatorio factory invalid type raises value error."""
    with patch(
        "relatorios.services.factory.relatorio_factory.ConfiguracaoRelatorio.objects.get"
    ) as mock_get:
        with patch(
            "relatorios.services.factory.relatorio_factory.Parametrizacao.objects.first"
        ) as mock_first:
            mock_get.return_value = object()
            mock_first.return_value = object()
            with pytest.raises(ValueError, match="não é um relatório válido"):
                RelatorioFactory.obter_relatorio("tipo_invalido")


def test_relatorio_factory_creates_service_for_valid_type() -> None:
    """Verifica relatorio factory creates service for valid type."""
    ConfiguracaoRelatorio.objects.get_or_create(tipo="LISTA_CANDIDATOS_SESSAO")
    Parametrizacao.objects.get_or_create(cabecalho="cabecalho")
    service = RelatorioFactory.obter_relatorio("LISTA_CANDIDATOS_SESSAO")
    from relatorios.services.relatorios.lista_candidatos_sessao import (
        ListaCandidatosSessao,
    )

    assert isinstance(service, ListaCandidatosSessao)
