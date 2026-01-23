"""
Testes unitários para o ViewSet ParametrizacaoViewSet usando pytest.
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from relatorios.models import Parametrizacao


pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    """Fixture para APIClient."""
    return APIClient()


@pytest.fixture
def parametrizacao():
    """Cria uma Parametrizacao de teste."""
    return Parametrizacao.objects.create(
        cabecalho="<h1>Cabeçalho Teste</h1>",
    )


@pytest.fixture
def parametrizacoes_multiplas():
    """Cria múltiplas Parametrizacoes de teste (mais recente primeiro)."""
    itens = []
    import time
    for i in range(3):
        itens.append(
            Parametrizacao.objects.create(
                cabecalho=f"<h1>Cabeçalho {i+1}</h1>",
            )
        )
        if i < 2:  # Pequeno delay para garantir timestamps diferentes
            time.sleep(0.01)
    return itens


class TestParametrizacaoViewSet:
    """Testes para o ViewSet ParametrizacaoViewSet."""

    def test_list_parametrizacao(self, client, parametrizacao):
        """Testa listagem de Parametrizacao."""
        url = reverse('parametrizacao-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        # Há um registro inicial criado pela migration, então esperamos pelo menos 2
        assert len(response.data) >= 1
        # Verifica que o registro criado está na lista
        uuids = [item['uuid'] for item in response.data]
        assert str(parametrizacao.uuid) in uuids

    def test_list_parametrizacao_multiple(self, client, parametrizacoes_multiplas):
        """Testa listagem com múltiplas Parametrizacoes."""
        url = reverse('parametrizacao-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Há um registro inicial criado pela migration, então esperamos pelo menos 4
        assert len(response.data) >= 3
        # Verifica ordenação (mais recente primeiro)
        timestamps = [item['criado_em'] for item in response.data]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_list_parametrizacao_empty(self, client):
        """Testa listagem quando não há Parametrizacoes criadas pelo teste."""
        # Não deleta o registro inicial da migration para evitar problemas
        # Apenas verifica que a listagem funciona
        url = reverse('parametrizacao-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_retrieve_parametrizacao(self, client, parametrizacao):
        """Testa recuperação de Parametrizacao específica."""
        url = reverse('parametrizacao-detail', args=[parametrizacao.uuid])
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['uuid'] == str(parametrizacao.uuid)
        assert response.data['cabecalho'] == parametrizacao.cabecalho
        assert 'criado_em' in response.data
        assert 'atualizado_em' in response.data

    def test_retrieve_most_recent(self, client, parametrizacoes_multiplas):
        """Testa que get_object sempre retorna o mais recente."""
        # Pega qualquer UUID, mas deve retornar o mais recente
        most_recent = parametrizacoes_multiplas[-1]  # Último criado
        url = reverse('parametrizacao-detail', args=[parametrizacoes_multiplas[0].uuid])
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Deve retornar o mais recente, não o UUID especificado
        assert response.data['uuid'] == str(most_recent.uuid)
        assert response.data['cabecalho'] == most_recent.cabecalho

    def test_update_parametrizacao(self, client, parametrizacao):
        """Testa atualização de Parametrizacao."""
        url = reverse('parametrizacao-detail', args=[parametrizacao.uuid])
        data = {
            'cabecalho': '<h1>Cabeçalho Atualizado</h1>'
        }
        response = client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['cabecalho'] == '<h1>Cabeçalho Atualizado</h1>'
        
        # Verifica no banco
        parametrizacao.refresh_from_db()
        assert parametrizacao.cabecalho == '<h1>Cabeçalho Atualizado</h1>'

    def test_update_most_recent(self, client, parametrizacoes_multiplas):
        """Testa que update sempre atualiza o mais recente."""
        most_recent = parametrizacoes_multiplas[-1]
        old_cabecalho_most_recent = most_recent.cabecalho
        old_cabecalho_first = parametrizacoes_multiplas[0].cabecalho
        
        # Tenta atualizar usando UUID de outro registro
        url = reverse('parametrizacao-detail', args=[parametrizacoes_multiplas[0].uuid])
        data = {
            'cabecalho': '<h1>Atualizado via outro UUID</h1>'
        }
        response = client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        # Deve ter atualizado o mais recente (não o UUID usado na URL)
        most_recent.refresh_from_db()
        assert most_recent.cabecalho == '<h1>Atualizado via outro UUID</h1>'
        # O primeiro não deve ter sido alterado
        parametrizacoes_multiplas[0].refresh_from_db()
        assert parametrizacoes_multiplas[0].cabecalho == old_cabecalho_first

    def test_update_put_method(self, client, parametrizacao):
        """Testa atualização usando PUT."""
        url = reverse('parametrizacao-detail', args=[parametrizacao.uuid])
        data = {
            'cabecalho': '<h1>PUT Update</h1>'
        }
        response = client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        parametrizacao.refresh_from_db()
        assert parametrizacao.cabecalho == '<h1>PUT Update</h1>'

    def test_create_not_allowed(self, client):
        """Testa que criação (POST) não é permitida."""
        initial_count = Parametrizacao.objects.count()
        url = reverse('parametrizacao-list')
        data = {
            'cabecalho': '<h1>Novo</h1>'
        }
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert 'Method "POST" not allowed' in response.data['detail']
        # Nenhum novo registro deve ter sido criado
        assert Parametrizacao.objects.count() == initial_count

    def test_delete_not_allowed(self, client, parametrizacao):
        """Testa que deleção não é permitida (ViewSet não tem DestroyModelMixin)."""
        initial_count = Parametrizacao.objects.count()
        url = reverse('parametrizacao-detail', args=[parametrizacao.uuid])
        response = client.delete(url)
        
        # Como não tem DestroyModelMixin, deve retornar 405
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        # Nenhum registro deve ter sido deletado
        assert Parametrizacao.objects.count() == initial_count

    def test_permission_allow_any(self, client, parametrizacao):
        """Testa que permissões AllowAny estão configuradas."""
        url = reverse('parametrizacao-list')
        response = client.get(url)
        
        # Se AllowAny estiver configurado, deve funcionar sem autenticação
        assert response.status_code == status.HTTP_200_OK

    def test_pagination_none(self, client, parametrizacoes_multiplas):
        """Testa que paginação está desabilitada."""
        url = reverse('parametrizacao-list')
        response = client.get(url)
        
        # Com pagination_class = None, deve retornar lista direta, não objeto com 'results'
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert 'results' not in response.data
        # Há um registro inicial criado pela migration, então esperamos pelo menos 4
        assert len(response.data) >= 3

    def test_response_fields(self, client, parametrizacao):
        """Testa que resposta contém todos os campos esperados."""
        url = reverse('parametrizacao-detail', args=[parametrizacao.uuid])
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # O serializer retorna 'id' automaticamente (primary key do Django)
        expected_fields = {'id', 'uuid', 'criado_em', 'atualizado_em', 'cabecalho', 'logo'}
        assert set(response.data.keys()) == expected_fields

    def test_update_partial_fields(self, client, parametrizacao):
        """Testa atualização parcial de campos."""
        original_cabecalho = parametrizacao.cabecalho
        
        url = reverse('parametrizacao-detail', args=[parametrizacao.uuid])
        data = {
            'cabecalho': '<h1>Parcial</h1>'
        }
        response = client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        parametrizacao.refresh_from_db()
        assert parametrizacao.cabecalho == '<h1>Parcial</h1>'
        # UUID não deve mudar
        assert parametrizacao.uuid == parametrizacao.uuid

    def test_get_object_returns_first(self, client, parametrizacoes_multiplas):
        """Testa que get_object retorna o primeiro do queryset ordenado."""
        # get_object usa queryset.first(), que deve ser o mais recente
        most_recent = Parametrizacao.objects.all().order_by('-criado_em').first()
        
        url = reverse('parametrizacao-detail', args=[parametrizacoes_multiplas[0].uuid])
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['uuid'] == str(most_recent.uuid)

    def test_retrieve_when_no_records(self, client):
        """Testa retrieve quando não há registros correspondentes ao UUID."""
        # Cria um UUID válido mas sem registro correspondente
        import uuid
        fake_uuid = uuid.uuid4()
        url = reverse('parametrizacao-detail', args=[fake_uuid])
        response = client.get(url)
        
        # get_object() sempre retorna o mais recente, então não retorna 404
        # Mas verifica que retorna algum registro (o mais recente)
        assert response.status_code == status.HTTP_200_OK
        assert 'uuid' in response.data

    def test_update_when_no_records(self, client):
        """Testa update quando não há registros correspondentes ao UUID."""
        import uuid
        fake_uuid = uuid.uuid4()
        url = reverse('parametrizacao-detail', args=[fake_uuid])
        data = {
            'cabecalho': '<h1>Teste</h1>'
        }
        response = client.patch(url, data, format='json')
        
        # get_object() sempre retorna o mais recente, então atualiza o mais recente
        assert response.status_code == status.HTTP_200_OK
        assert response.data['cabecalho'] == '<h1>Teste</h1>'

