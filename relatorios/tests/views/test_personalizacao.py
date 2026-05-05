"""
Testes unitários para o PersonalizacaoViewSet.
"""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from relatorios.models import ConfiguracaoRelatorio


pytestmark = pytest.mark.django_db

CAMPOS_ESPERADOS = [
    'uuid', 'tipo', 'usar_logotipo',
    'cabecalho', 'cabecalho_gabarito', 'cabecalho_capa_ata',
    'texto_final', 'criado_em', 'atualizado_em',
]


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def configuracao_lauda_vagas():
    config, _ = ConfiguracaoRelatorio.objects.get_or_create(tipo='LAUDA_VAGAS')
    config.cabecalho = '<h1>Cabeçalho</h1>'
    config.cabecalho_gabarito = '<h1>Gabarito Lauda</h1>'
    config.texto_final = '<p>Rodapé</p>'
    config.save()
    return config


@pytest.fixture
def configuracao_ata_escolha():
    config, _ = ConfiguracaoRelatorio.objects.get_or_create(tipo='ATA_ESCOLHA')
    config.cabecalho_gabarito = '<h1>Gabarito Ata</h1>'
    config.cabecalho_capa_ata = '<h2>Capa da Ata</h2>'
    config.save()
    return config


class TestPersonalizacaoListagem:

    def test_list_retorna_200(self, client, configuracao_lauda_vagas):
        url = reverse('personalizacao-list')
        response = client.get(url, {'tipo': 'LAUDA_VAGAS'})
        assert response.status_code == status.HTTP_200_OK

    def test_list_retorna_cabecalho_gabarito(self, client, configuracao_lauda_vagas):
        url = reverse('personalizacao-list')
        response = client.get(url, {'tipo': 'LAUDA_VAGAS'})
        assert response.data['cabecalho_gabarito'] == '<h1>Gabarito Lauda</h1>'

    def test_list_retorna_todos_campos_esperados(self, client, configuracao_lauda_vagas):
        url = reverse('personalizacao-list')
        response = client.get(url, {'tipo': 'LAUDA_VAGAS'})
        for campo in CAMPOS_ESPERADOS:
            assert campo in response.data, f"Campo '{campo}' ausente na resposta"

    def test_list_sem_filtro_retorna_primeira_configuracao(self, client, configuracao_lauda_vagas):
        url = reverse('personalizacao-list')
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'cabecalho_gabarito' in response.data

    def test_list_tipo_invalido_retorna_400(self, client):
        url = reverse('personalizacao-list')
        response = client.get(url, {'tipo': 'TIPO_INEXISTENTE'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestPersonalizacaoAtualizacao:

    def test_patch_atualiza_cabecalho_gabarito(self, client, configuracao_lauda_vagas):
        url = reverse('personalizacao-detail', kwargs={'uuid': str(configuracao_lauda_vagas.uuid)})
        novo_gabarito = '<h2>Gabarito Atualizado</h2>'
        response = client.patch(url, {'cabecalho_gabarito': novo_gabarito}, format='json')
        assert response.status_code == status.HTTP_200_OK
        configuracao_lauda_vagas.refresh_from_db()
        assert configuracao_lauda_vagas.cabecalho_gabarito == novo_gabarito

    def test_patch_retorna_cabecalho_gabarito_atualizado(self, client, configuracao_lauda_vagas):
        url = reverse('personalizacao-detail', kwargs={'uuid': str(configuracao_lauda_vagas.uuid)})
        novo_gabarito = '<h2>Retorno Gabarito</h2>'
        response = client.patch(url, {'cabecalho_gabarito': novo_gabarito}, format='json')
        assert response.data['cabecalho_gabarito'] == novo_gabarito

    def test_patch_limpa_cabecalho_gabarito(self, client, configuracao_lauda_vagas):
        url = reverse('personalizacao-detail', kwargs={'uuid': str(configuracao_lauda_vagas.uuid)})
        response = client.patch(url, {'cabecalho_gabarito': ''}, format='json')
        assert response.status_code == status.HTTP_200_OK
        configuracao_lauda_vagas.refresh_from_db()
        assert configuracao_lauda_vagas.cabecalho_gabarito == ''

    def test_patch_cabecalho_gabarito_nao_afeta_outros_campos(self, client, configuracao_lauda_vagas):
        url = reverse('personalizacao-detail', kwargs={'uuid': str(configuracao_lauda_vagas.uuid)})
        response = client.patch(url, {'cabecalho_gabarito': '<h2>Só gabarito</h2>'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        configuracao_lauda_vagas.refresh_from_db()
        assert configuracao_lauda_vagas.cabecalho == '<h1>Cabeçalho</h1>'
        assert configuracao_lauda_vagas.texto_final == '<p>Rodapé</p>'

    def test_patch_multiples_campos_com_gabarito(self, client, configuracao_lauda_vagas):
        url = reverse('personalizacao-detail', kwargs={'uuid': str(configuracao_lauda_vagas.uuid)})
        payload = {
            'cabecalho': '<h1>Cabeçalho Novo</h1>',
            'cabecalho_gabarito': '<h1>Gabarito Novo</h1>',
            'usar_logotipo': True,
        }
        response = client.patch(url, payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        configuracao_lauda_vagas.refresh_from_db()
        assert configuracao_lauda_vagas.cabecalho == '<h1>Cabeçalho Novo</h1>'
        assert configuracao_lauda_vagas.cabecalho_gabarito == '<h1>Gabarito Novo</h1>'
        assert configuracao_lauda_vagas.usar_logotipo is True

    def test_patch_ata_escolha_com_cabecalho_gabarito_e_capa(self, client, configuracao_ata_escolha):
        url = reverse('personalizacao-detail', kwargs={'uuid': str(configuracao_ata_escolha.uuid)})
        payload = {
            'cabecalho_gabarito': '<h1>Gabarito Ata Atualizado</h1>',
            'cabecalho_capa_ata': '<h2>Nova Capa</h2>',
        }
        response = client.patch(url, payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        configuracao_ata_escolha.refresh_from_db()
        assert configuracao_ata_escolha.cabecalho_gabarito == '<h1>Gabarito Ata Atualizado</h1>'
        assert configuracao_ata_escolha.cabecalho_capa_ata == '<h2>Nova Capa</h2>'

    def test_patch_uuid_nao_alteravel(self, client, configuracao_lauda_vagas):
        url = reverse('personalizacao-detail', kwargs={'uuid': str(configuracao_lauda_vagas.uuid)})
        uuid_original = str(configuracao_lauda_vagas.uuid)
        response = client.patch(url, {'uuid': 'outro-uuid'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert str(response.data['uuid']) == uuid_original

    def test_patch_uuid_inexistente_retorna_404(self, client):
        import uuid
        url = reverse('personalizacao-detail', kwargs={'uuid': str(uuid.uuid4())})
        response = client.patch(url, {'cabecalho_gabarito': '<h1>x</h1>'}, format='json')
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestPersonalizacaoFiltragemPorTipo:

    def test_filtro_tipo_retorna_configuracao_correta(self, client, configuracao_lauda_vagas, configuracao_ata_escolha):
        url = reverse('personalizacao-list')
        response = client.get(url, {'tipo': 'ATA_ESCOLHA'})
        assert response.data['cabecalho_gabarito'] == '<h1>Gabarito Ata</h1>'

    def test_filtro_tipo_lauda_vagas(self, client, configuracao_lauda_vagas, configuracao_ata_escolha):
        url = reverse('personalizacao-list')
        response = client.get(url, {'tipo': 'LAUDA_VAGAS'})
        assert response.data['cabecalho_gabarito'] == '<h1>Gabarito Lauda</h1>'
