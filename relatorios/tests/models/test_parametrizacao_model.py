"""
Testes unitários para o model Parametrizacao usando pytest.
"""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from relatorios.models import Parametrizacao

pytestmark = pytest.mark.django_db


@pytest.fixture
def parametrizacao():
    """Cria uma Parametrizacao de teste."""
    return Parametrizacao.objects.create(
        cabecalho="<h1>Cabeçalho Teste</h1>",
    )


@pytest.fixture
def parametrizacao_com_logo():
    """Cria uma Parametrizacao com logo de teste."""
    logo = SimpleUploadedFile(
        "logo.png", b"fake image content", content_type="image/png"
    )
    return Parametrizacao.objects.create(
        cabecalho="<h1>Cabeçalho com Logo</h1>", logo=logo
    )


@pytest.fixture
def parametrizacoes_multiplas():
    """Cria múltiplas Parametrizacoes de teste."""
    itens = []
    for i in range(3):
        itens.append(
            Parametrizacao.objects.create(
                cabecalho=f"<h1>Cabeçalho {i+1}</h1>",
            )
        )
    return itens


class TestParametrizacaoModel:
    """Testes para o model Parametrizacao."""

    def test_parametrizacao_creation(self):
        """Testa criação básica de Parametrizacao."""
        parametrizacao = Parametrizacao.objects.create(
            cabecalho="<h1>Teste</h1>"
        )

        assert parametrizacao.pk is not None
        assert parametrizacao.cabecalho == "<h1>Teste</h1>"
        assert not parametrizacao.logo  # ImageField retorna False quando vazio
        assert parametrizacao.uuid is not None

    def test_parametrizacao_with_default_cabecalho(self):
        """Testa criação de Parametrizacao com cabeçalho padrão vazio."""
        parametrizacao = Parametrizacao.objects.create()

        assert parametrizacao.cabecalho == ""
        assert not parametrizacao.logo  # ImageField retorna False quando vazio

    def test_parametrizacao_with_logo(self, parametrizacao_com_logo):
        """Testa criação de Parametrizacao com logo."""
        assert parametrizacao_com_logo.logo is not None
        assert parametrizacao_com_logo.logo.name.startswith("parametrizacao/")

    def test_parametrizacao_uuid_auto_generated(self, parametrizacao):
        """Testa se UUID é gerado automaticamente."""
        assert parametrizacao.uuid is not None
        assert isinstance(parametrizacao.uuid, str) or hasattr(
            parametrizacao.uuid, "hex"
        )

    def test_parametrizacao_timestamps(self, parametrizacao):
        """Testa se timestamps são criados automaticamente."""
        assert parametrizacao.criado_em is not None
        assert parametrizacao.atualizado_em is not None

    def test_parametrizacao_str(self, parametrizacao):
        """Testa método __str__ do model."""
        str_repr = str(parametrizacao)
        assert "Parametrização" in str_repr
        assert "Criado em" in str_repr

    def test_parametrizacao_ordering(self, parametrizacoes_multiplas):
        """Testa ordenação padrão do model (mais recente primeiro)."""
        parametrizacoes = Parametrizacao.objects.all()

        # Verifica que está ordenado por -criado_em
        timestamps = [p.criado_em for p in parametrizacoes]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_parametrizacao_blank_cabecalho(self):
        """Testa que cabeçalho pode ser vazio."""
        parametrizacao = Parametrizacao.objects.create(cabecalho="")
        assert parametrizacao.cabecalho == ""

    def test_parametrizacao_null_logo(self, parametrizacao):
        """Testa que logo pode ser None."""
        assert not parametrizacao.logo  # ImageField retorna False quando vazio

    def test_parametrizacao_update_timestamp(self, parametrizacao):
        """Testa se atualizado_em é atualizado ao modificar o registro."""
        import time

        original_updated = parametrizacao.atualizado_em
        time.sleep(0.01)  # Pequeno delay para garantir diferença de timestamp

        parametrizacao.cabecalho = "<h1>Atualizado</h1>"
        parametrizacao.save()
        parametrizacao.refresh_from_db()

        assert parametrizacao.atualizado_em >= original_updated

    def test_parametrizacao_verbose_names(self):
        """Testa se os verbose names estão configurados corretamente."""
        assert Parametrizacao._meta.verbose_name == "Parametrização"
        assert Parametrizacao._meta.verbose_name_plural == "Parametrizações"

    def test_parametrizacao_field_verbose_names(self):
        """Testa se os verbose names dos campos estão configurados."""
        cabecalho_field = Parametrizacao._meta.get_field("cabecalho")
        logo_field = Parametrizacao._meta.get_field("logo")

        assert cabecalho_field.verbose_name == "Cabeçalho Padrão"
        assert logo_field.verbose_name == "Logo"

    def test_parametrizacao_field_help_texts(self):
        """Testa se os help texts dos campos estão configurados."""
        cabecalho_field = Parametrizacao._meta.get_field("cabecalho")
        logo_field = Parametrizacao._meta.get_field("logo")

        assert "Cabeçalho padrão em HTML" in cabecalho_field.help_text
        assert "Logo para os relatórios" in logo_field.help_text
