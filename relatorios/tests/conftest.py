"""
Configuração para testes do app relatorios.
"""
import pytest
import uuid

from ..models import Relatorio


@pytest.fixture
def relatorio():
    """Cria um Relatorio de teste."""
    return Relatorio.objects.create(
        nome="Relatório Teste",
        tipo="agenda",
    )


@pytest.fixture
def relatorios_multiplos():
    """Cria múltiplos Relatorios de teste."""
    itens = []
    for i in range(3):
        itens.append(
            Relatorio.objects.create(
                nome=f"Relatório {i+1}",
                tipo="agenda",
            )
        )
    return itens
