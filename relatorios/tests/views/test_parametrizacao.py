"""Testes unitários para o ViewSet ParametrizacaoViewSet usando pytest."""
from __future__ import annotations
from typing import Any
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from relatorios.models import Parametrizacao
pytestmark = pytest.mark.django_db

@pytest.fixture
def client() -> Any:
    """Fixture para APIClient."""
    return APIClient()

@pytest.fixture
def parametrizacao() -> Any:
    """Cria uma Parametrizacao de teste."""
    return Parametrizacao.objects.create(cabecalho='<h1>Cabeçalho Teste</h1>')

@pytest.fixture
def parametrizacoes_multiplas() -> Any:
    """Cria múltiplas Parametrizacoes de teste (mais recente primeiro)."""
    itens = []
    import time
    for i in range(3):
        itens.append(Parametrizacao.objects.create(cabecalho=f'<h1>Cabeçalho {i + 1}</h1>'))
        if i < 2:
            time.sleep(0.01)
    return itens

class TestParametrizacaoViewSet:
    """Testes para o ViewSet ParametrizacaoViewSet."""

    def test_list_parametrizacao(self, client: Any, parametrizacao: Any) -> None:
        """Testa listagem de Parametrizacao."""
        url = reverse('parametrizacao-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) >= 1
        uuids = [item['uuid'] for item in response.data]
        assert str(parametrizacao.uuid) in uuids

    def test_list_parametrizacao_multiple(self, client: Any, parametrizacoes_multiplas: Any) -> None:
        """Testa listagem com múltiplas Parametrizacoes."""
        url = reverse('parametrizacao-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 3
        timestamps = [item['criado_em'] for item in response.data]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_list_parametrizacao_empty(self, client: Any) -> None:
        """Testa listagem quando não há Parametrizacoes criadas pelo teste."""
        url = reverse('parametrizacao-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_retrieve_parametrizacao(self, client: Any, parametrizacao: Any) -> None:
        """Testa recuperação de Parametrizacao específica."""
        url = reverse('parametrizacao-detail', args=[parametrizacao.uuid])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['uuid'] == str(parametrizacao.uuid)
        assert response.data['cabecalho'] == parametrizacao.cabecalho
        assert 'criado_em' in response.data
        assert 'atualizado_em' in response.data

    def test_retrieve_most_recent(self, client: Any, parametrizacoes_multiplas: Any) -> None:
        """Testa que get_object sempre retorna o mais recente."""
        most_recent = parametrizacoes_multiplas[-1]
        url = reverse('parametrizacao-detail', args=[parametrizacoes_multiplas[0].uuid])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['uuid'] == str(most_recent.uuid)
        assert response.data['cabecalho'] == most_recent.cabecalho

    def test_update_parametrizacao(self, client: Any, parametrizacao: Any) -> None:
        """Testa atualização de Parametrizacao."""
        url = reverse('parametrizacao-detail', args=[parametrizacao.uuid])
        data = {'cabecalho': '<h1>Cabeçalho Atualizado</h1>'}
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['cabecalho'] == '<h1>Cabeçalho Atualizado</h1>'
        parametrizacao.refresh_from_db()
        assert parametrizacao.cabecalho == '<h1>Cabeçalho Atualizado</h1>'

    def test_update_most_recent(self, client: Any, parametrizacoes_multiplas: Any) -> None:
        """Testa que update sempre atualiza o mais recente."""
        most_recent = parametrizacoes_multiplas[-1]
        old_cabecalho_first = parametrizacoes_multiplas[0].cabecalho
        url = reverse('parametrizacao-detail', args=[parametrizacoes_multiplas[0].uuid])
        data = {'cabecalho': '<h1>Atualizado via outro UUID</h1>'}
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        most_recent.refresh_from_db()
        assert most_recent.cabecalho == '<h1>Atualizado via outro UUID</h1>'
        parametrizacoes_multiplas[0].refresh_from_db()
        assert parametrizacoes_multiplas[0].cabecalho == old_cabecalho_first

    def test_update_put_method(self, client: Any, parametrizacao: Any) -> None:
        """Testa atualização usando PUT."""
        url = reverse('parametrizacao-detail', args=[parametrizacao.uuid])
        data = {'cabecalho': '<h1>PUT Update</h1>'}
        response = client.put(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        parametrizacao.refresh_from_db()
        assert parametrizacao.cabecalho == '<h1>PUT Update</h1>'

    def test_create_not_allowed(self, client: Any) -> None:
        """Testa que criação (POST) não é permitida."""
        initial_count = Parametrizacao.objects.count()
        url = reverse('parametrizacao-list')
        data = {'cabecalho': '<h1>Novo</h1>'}
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert 'Method "POST" not allowed' in response.data['detail']
        assert Parametrizacao.objects.count() == initial_count

    def test_delete_not_allowed(self, client: Any, parametrizacao: Any) -> None:
        """Testa que deleção não é permitida (ViewSet não tem DestroyModelMixin)."""
        initial_count = Parametrizacao.objects.count()
        url = reverse('parametrizacao-detail', args=[parametrizacao.uuid])
        response = client.delete(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert Parametrizacao.objects.count() == initial_count

    def test_permission_allow_any(self, client: Any, parametrizacao: Any) -> None:
        """Testa que permissões AllowAny estão configuradas."""
        url = reverse('parametrizacao-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_pagination_none(self, client: Any, parametrizacoes_multiplas: Any) -> None:
        """Testa que paginação está desabilitada."""
        url = reverse('parametrizacao-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert 'results' not in response.data
        assert len(response.data) >= 3

    def test_response_fields(self, client: Any, parametrizacao: Any) -> None:
        """Testa que resposta contém todos os campos esperados."""
        url = reverse('parametrizacao-detail', args=[parametrizacao.uuid])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        expected_fields = {'id', 'uuid', 'criado_em', 'atualizado_em', 'cabecalho', 'logo'}
        assert set(response.data.keys()) == expected_fields

    def test_update_partial_fields(self, client: Any, parametrizacao: Any) -> None:
        """Testa atualização parcial de campos."""
        url = reverse('parametrizacao-detail', args=[parametrizacao.uuid])
        data = {'cabecalho': '<h1>Parcial</h1>'}
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        parametrizacao.refresh_from_db()
        assert parametrizacao.cabecalho == '<h1>Parcial</h1>'
        assert parametrizacao.uuid == parametrizacao.uuid

    def test_get_object_returns_first(self, client: Any, parametrizacoes_multiplas: Any) -> None:
        """Testa que get_object retorna o primeiro do queryset ordenado."""
        most_recent = Parametrizacao.objects.all().order_by('-criado_em').first()
        url = reverse('parametrizacao-detail', args=[parametrizacoes_multiplas[0].uuid])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['uuid'] == str(most_recent.uuid)  # type: ignore[union-attr]

    def test_retrieve_when_no_records(self, client: Any) -> None:
        """Testa retrieve quando não há registros correspondentes ao UUID."""
        import uuid
        fake_uuid = uuid.uuid4()
        url = reverse('parametrizacao-detail', args=[fake_uuid])
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'uuid' in response.data

    def test_update_when_no_records(self, client: Any) -> None:
        """Testa update quando não há registros correspondentes ao UUID."""
        import uuid
        fake_uuid = uuid.uuid4()
        url = reverse('parametrizacao-detail', args=[fake_uuid])
        data = {'cabecalho': '<h1>Teste</h1>'}
        response = client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['cabecalho'] == '<h1>Teste</h1>'
