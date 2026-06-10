"""Configuração para testes do app relatorios."""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from ..models import Relatorio


@pytest.fixture(autouse=True)
def _remove_sigla_sdk_middlewares_for_tests(settings: Any) -> None:
    """Remove sigla sdk middlewares for tests."""
    settings.MIDDLEWARE = [
        m
        for m in settings.MIDDLEWARE
        if not m.startswith("sigla_sdk.middlewares.")
    ]


@pytest.fixture
def relatorio() -> Any:
    """Cria um Relatorio de teste."""
    return Relatorio.objects.create(
        tipo="agenda",
        usuario="tester",
        dados={"foo": "bar"},
        processo_uuid=uuid.uuid4(),
        cabecalho="<b>Cabeçalho</b>",
    )


@pytest.fixture
def relatorios_multiplos() -> Any:
    """Cria múltiplos Relatorios de teste."""
    itens = []
    for i in range(3):
        itens.append(
            Relatorio.objects.create(
                tipo="agenda",
                usuario=f"user{i + 1}",
                dados={"idx": i + 1},
                processo_uuid=uuid.uuid4(),
                cabecalho=None,
            )
        )
    return itens
