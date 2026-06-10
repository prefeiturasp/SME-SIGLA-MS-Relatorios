"""Testes unitários para o serializer ParametrizacaoSerializer usando."""

from __future__ import annotations

from typing import Any

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from relatorios.models import Parametrizacao
from relatorios.serializers import ParametrizacaoSerializer

pytestmark = pytest.mark.django_db


@pytest.fixture
def parametrizacao() -> Any:
    """Cria uma Parametrizacao de teste."""
    return Parametrizacao.objects.create(cabecalho="<h1>Cabeçalho Teste</h1>")


@pytest.fixture
def parametrizacao_com_logo() -> Any:
    """Cria uma Parametrizacao com logo de teste."""
    logo = SimpleUploadedFile(
        "logo.png", b"fake image content", content_type="image/png"
    )
    return Parametrizacao.objects.create(
        cabecalho="<h1>Cabeçalho com Logo</h1>", logo=logo
    )


class TestParametrizacaoSerializer:
    """Testes para o serializer ParametrizacaoSerializer."""

    def test_serializer_serialization(self, parametrizacao: Any) -> None:
        """Verifica serializer serialization."""
        serializer = ParametrizacaoSerializer(parametrizacao)
        data = serializer.data
        assert "uuid" in data
        assert "criado_em" in data
        assert "atualizado_em" in data
        assert "cabecalho" in data
        assert "logo" in data
        assert data["cabecalho"] == "<h1>Cabeçalho Teste</h1>"
        assert data["uuid"] == str(parametrizacao.uuid)

    def test_serializer_serialization_with_logo(
        self, parametrizacao_com_logo: Any
    ) -> None:
        """Verifica serializer serialization with logo."""
        serializer = ParametrizacaoSerializer(parametrizacao_com_logo)
        data = serializer.data
        assert data["logo"] is not None
        assert "parametrizacao" in data["logo"] or data["logo"] == ""

    def test_serializer_deserialization_create(self) -> None:
        """Verifica serializer deserialization create."""
        data = {"cabecalho": "<div>Novo Cabeçalho</div>"}
        serializer = ParametrizacaoSerializer(data=data)
        assert serializer.is_valid()
        parametrizacao = serializer.save()
        assert parametrizacao.cabecalho == "<div>Novo Cabeçalho</div>"
        assert parametrizacao.pk is not None

    def test_serializer_deserialization_with_empty_cabecalho(self) -> None:
        """Verifica serializer deserialization with empty cabecalho."""
        data = {"cabecalho": ""}
        serializer = ParametrizacaoSerializer(data=data)
        assert serializer.is_valid()
        parametrizacao = serializer.save()
        assert parametrizacao.cabecalho == ""

    def test_serializer_read_only_fields(self, parametrizacao: Any) -> None:
        """Verifica serializer read only fields."""
        data = {
            "uuid": "00000000-0000-0000-0000-000000000000",
            "criado_em": "2020-01-01T00:00:00Z",
            "atualizado_em": "2020-01-01T00:00:00Z",
            "cabecalho": "<h1>Novo</h1>",
        }
        serializer = ParametrizacaoSerializer(
            parametrizacao, data=data, partial=True
        )
        assert serializer.is_valid()
        updated = serializer.save()
        assert str(updated.uuid) != "00000000-0000-0000-0000-000000000000"
        assert updated.uuid == parametrizacao.uuid
        assert updated.criado_em == parametrizacao.criado_em
        assert updated.cabecalho == "<h1>Novo</h1>"

    def test_serializer_update(self, parametrizacao: Any) -> None:
        """Verifica serializer update."""
        data = {"cabecalho": "<h1>Cabeçalho Atualizado</h1>"}
        serializer = ParametrizacaoSerializer(
            parametrizacao, data=data, partial=True
        )
        assert serializer.is_valid()
        updated = serializer.save()
        assert updated.cabecalho == "<h1>Cabeçalho Atualizado</h1>"
        assert updated.uuid == parametrizacao.uuid

    def test_serializer_all_fields(self, parametrizacao: Any) -> None:
        """Verifica serializer all fields."""
        serializer = ParametrizacaoSerializer(parametrizacao)
        data = serializer.data
        expected_fields = {
            "id",
            "uuid",
            "criado_em",
            "atualizado_em",
            "cabecalho",
            "logo",
        }
        assert set(data.keys()) == expected_fields

    def test_serializer_with_html_content(self) -> None:
        """Verifica serializer with html content."""
        html_content = '\n        <div>\n            <h1>Título</h1>\n            <p>Parágrafo com <strong>negrito</strong></p>\n            <img src="logo.png" alt="Logo">\n        </div>\n        '  # noqa: E501
        data = {"cabecalho": html_content}
        serializer = ParametrizacaoSerializer(data=data)
        assert serializer.is_valid()
        parametrizacao = serializer.save()
        assert parametrizacao.cabecalho == html_content.strip()

    def test_serializer_partial_update(self, parametrizacao: Any) -> None:
        """Verifica serializer partial update."""
        data = {"cabecalho": "<h1>Parcial</h1>"}
        serializer = ParametrizacaoSerializer(
            parametrizacao, data=data, partial=True
        )
        assert serializer.is_valid()
        updated = serializer.save()
        assert updated.cabecalho == "<h1>Parcial</h1>"
        assert updated.uuid == parametrizacao.uuid
        assert updated.criado_em == parametrizacao.criado_em

    def test_serializer_validation_valid_data(self) -> None:
        """Verifica serializer validation valid data."""
        data = {"cabecalho": "<h1>Válido</h1>"}
        serializer = ParametrizacaoSerializer(data=data)
        assert serializer.is_valid()

    def test_serializer_meta_model(self) -> None:
        """Verifica serializer meta model."""
        assert ParametrizacaoSerializer.Meta.model == Parametrizacao

    def test_serializer_meta_fields(self) -> None:
        """Verifica serializer meta fields."""
        assert ParametrizacaoSerializer.Meta.fields == "__all__"

    def test_serializer_meta_read_only_fields(self) -> None:
        """Verifica serializer meta read only fields."""
        read_only = ParametrizacaoSerializer.Meta.read_only_fields
        assert "uuid" in read_only
        assert "criado_em" in read_only
        assert "atualizado_em" in read_only
