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
        tipo="agenda",
        usuario="tester",
        dados={"foo": "bar"},
        processo_uuid=uuid.uuid4(),
        cabecalho="<b>Cabeçalho</b>",
    )


@pytest.fixture
def relatorios_multiplos():
    """Cria múltiplos Relatorios de teste."""
    itens = []
    for i in range(3):
        itens.append(
            Relatorio.objects.create(
                tipo="agenda",
                usuario=f"user{i+1}",
                dados={"idx": i + 1},
                processo_uuid=uuid.uuid4(),
                cabecalho=None,
            )
        )
    return itens
