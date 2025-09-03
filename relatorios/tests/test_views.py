"""
Testes unitários para as views do app relatorios usando pytest.
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from ..models import Relatorio
from ..serializers import RelatorioSerializer


pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def relatorio():
    return Relatorio.objects.create(
        nome="Relatório Lista",
        tipo="agenda",
    )


@pytest.fixture
def relatorios():
    itens = []
    for i in range(2):
        itens.append(
            Relatorio.objects.create(
                nome=f"Relatório {i+1}",
                tipo="agenda",
            )
        )
    return itens


# Testes para RelatorioViewSet

def test_relatorio_list(client, relatorio):
    url = reverse('relatorio-list')
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert 'results' in response.data
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['nome'] == relatorio.nome


def test_relatorio_create(client):
    url = reverse('relatorio-list')
    data = {
        'nome': 'Relatório Novo',
        'tipo': 'agenda',
    }

    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert Relatorio.objects.count() == 1

    item = Relatorio.objects.first()
    assert item.nome == 'Relatório Novo'
    assert item.tipo == 'agenda'


def test_relatorio_retrieve(client, relatorio):
    url = reverse('relatorio-detail', args=[relatorio.uuid])
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['nome'] == relatorio.nome
    assert response.data['uuid'] == str(relatorio.uuid)


def test_relatorio_update(client, relatorio):
    url = reverse('relatorio-detail', args=[relatorio.uuid])
    data = {
        'nome': 'Relatório Atualizado',
        'tipo': 'convocacao',
    }

    response = client.patch(url, data, format='json')

    assert response.status_code == status.HTTP_200_OK
    relatorio.refresh_from_db()
    assert relatorio.nome == 'Relatório Atualizado'
    assert relatorio.tipo == 'convocacao'


def test_relatorio_delete(client, relatorio):
    url = reverse('relatorio-detail', args=[relatorio.uuid])
    response = client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert Relatorio.objects.count() == 0
