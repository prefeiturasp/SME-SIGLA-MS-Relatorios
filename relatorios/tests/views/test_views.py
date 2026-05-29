"""
Testes unitários para as views do app relatorios usando pytest.
"""

import uuid
from unittest.mock import Mock, patch

import pytest
from django.http import HttpResponse
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from relatorios.models import Relatorio

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def relatorio():
    return Relatorio.objects.create(
        tipo="agenda",
        usuario="tester",
        dados={"foo": "bar"},
        processo_uuid=uuid.uuid4(),
        cabecalho="<b>Cabeçalho</b>",
    )


@pytest.fixture
def relatorios():
    itens = []
    for i in range(2):
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


# Testes para RelatorioViewSet


def test_relatorio_list(client, relatorio):
    url = reverse("relatorio-list")
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert len(response.data["results"]) == 1
    # Novos campos presentes no retorno
    assert response.data["results"][0]["tipo"] == relatorio.tipo
    assert response.data["results"][0]["usuario"] == relatorio.usuario
    assert "dados" in response.data["results"][0]
    assert "processo_uuid" in response.data["results"][0]
    assert "cabecalho" in response.data["results"][0]


@patch("relatorios.views.relatorios.RelatorioFactory.obter_relatorio")
def test_relatorio_create(mock_obter_relatorio, client):
    """Cria relatório com chamadas externas mockadas."""
    mock_service = Mock()
    mock_service.gerar.return_value = (
        HttpResponse("<html></html>", content_type="text/html"),
        {"k": "v"},
    )
    mock_obter_relatorio.return_value = mock_service

    url = reverse("relatorio-list")
    data = {
        "tipo": "LAUDA_VAGAS",
        "usuario": "criador",
        "dados": {"k": "v"},
        "processo_uuid": str(uuid.uuid4()),
        "cabecalho": "<p>header</p>",
    }

    response = client.post(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert Relatorio.objects.count() == 1

    item = Relatorio.objects.first()
    assert item.tipo == "LAUDA_VAGAS"
    assert item.usuario == "criador"
    assert str(item.processo_uuid) == data["processo_uuid"]
    assert item.cabecalho == "<p>header</p>"
    assert item.dados == {"k": "v"}
    mock_obter_relatorio.assert_called_once_with("LAUDA_VAGAS")
    mock_service.gerar.assert_called_once()


def test_relatorio_get(client, relatorio):
    url = reverse("relatorio-detail", args=[relatorio.pk])
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["uuid"] == str(relatorio.uuid)
    # Novos campos presentes no retrieve
    assert response.data["tipo"] == relatorio.tipo
    assert response.data["usuario"] == relatorio.usuario
    assert "dados" in response.data
    assert "processo_uuid" in response.data
    assert "cabecalho" in response.data


def test_relatorio_delete(client, relatorio):
    url = reverse("relatorio-detail", args=[relatorio.pk])
    response = client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Relatorio.objects.count() == 0
