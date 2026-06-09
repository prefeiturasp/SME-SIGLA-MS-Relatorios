"""Testes unitários para o serializer ConfiguracaoRelatorioSerializer."""
from __future__ import annotations
from typing import Any
import pytest
from relatorios.models import ConfiguracaoRelatorio
from relatorios.serializers import ConfiguracaoRelatorioSerializer
pytestmark = pytest.mark.django_db
CAMPOS_ESPERADOS = ['uuid', 'tipo', 'usar_logotipo', 'cabecalho', 'cabecalho_gabarito', 'cabecalho_capa_ata', 'texto_final', 'criado_em', 'atualizado_em']

@pytest.fixture
def configuracao() -> Any:
    """Executa configuracao."""
    config, _ = ConfiguracaoRelatorio.objects.get_or_create(tipo='LAUDA_VAGAS')
    config.cabecalho = '<h1>Cabeçalho</h1>'
    config.cabecalho_gabarito = '<h1>Gabarito</h1>'
    config.texto_final = '<p>Rodapé</p>'
    config.cabecalho_capa_ata = ''
    config.save()
    return config

class TestConfiguracaoRelatorioSerializer:
    """Define TestConfiguracaoRelatorioSerializer."""

    def test_campos_presentes_na_serializacao(self, configuracao: Any) -> None:
        """Verifica campos presentes na serializacao."""
        serializer = ConfiguracaoRelatorioSerializer(configuracao)
        for campo in CAMPOS_ESPERADOS:
            assert campo in serializer.data, f"Campo '{campo}' ausente na serialização"

    def test_uuid_somente_leitura(self, configuracao: Any) -> None:
        """Verifica uuid somente leitura."""
        serializer = ConfiguracaoRelatorioSerializer(configuracao, data={'uuid': 'novo-uuid', 'tipo': 'LAUDA_VAGAS'}, partial=True)
        assert serializer.is_valid()
        instance = serializer.save()
        assert str(instance.uuid) == str(configuracao.uuid)

    def test_serializacao_cabecalho_gabarito(self, configuracao: Any) -> None:
        """Verifica serializacao cabecalho gabarito."""
        serializer = ConfiguracaoRelatorioSerializer(configuracao)
        assert serializer.data['cabecalho_gabarito'] == '<h1>Gabarito</h1>'

    def test_serializacao_cabecalho_gabarito_vazio(self) -> None:
        """Verifica serializacao cabecalho gabarito vazio."""
        config, _ = ConfiguracaoRelatorio.objects.get_or_create(tipo='RELACAO_VAGAS')
        config.cabecalho_gabarito = ''
        config.save()
        serializer = ConfiguracaoRelatorioSerializer(config)
        assert serializer.data['cabecalho_gabarito'] == ''

    def test_desserializacao_cabecalho_gabarito(self, configuracao: Any) -> None:
        """Verifica desserializacao cabecalho gabarito."""
        novo_html = '<p>Novo Gabarito</p>'
        serializer = ConfiguracaoRelatorioSerializer(configuracao, data={'cabecalho_gabarito': novo_html}, partial=True)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.cabecalho_gabarito == novo_html

    def test_desserializacao_cabecalho_gabarito_vazio(self, configuracao: Any) -> None:
        """Verifica desserializacao cabecalho gabarito vazio."""
        serializer = ConfiguracaoRelatorioSerializer(configuracao, data={'cabecalho_gabarito': ''}, partial=True)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.cabecalho_gabarito == ''

    def test_atualizacao_parcial_nao_afeta_outros_campos(self, configuracao: Any) -> None:
        """Verifica atualizacao parcial nao afeta outros campos."""
        serializer = ConfiguracaoRelatorioSerializer(configuracao, data={'cabecalho_gabarito': '<h2>Só o gabarito</h2>'}, partial=True)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.cabecalho == '<h1>Cabeçalho</h1>'
        assert instance.texto_final == '<p>Rodapé</p>'
        assert instance.cabecalho_gabarito == '<h2>Só o gabarito</h2>'

    def test_atualizacao_multiplos_campos_incluindo_gabarito(self, configuracao: Any) -> None:
        """Verifica atualizacao multiplos campos incluindo gabarito."""
        serializer = ConfiguracaoRelatorioSerializer(configuracao, data={'cabecalho': '<h1>Novo Cabeçalho</h1>', 'cabecalho_gabarito': '<h1>Novo Gabarito</h1>', 'usar_logotipo': True}, partial=True)
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        assert instance.cabecalho == '<h1>Novo Cabeçalho</h1>'
        assert instance.cabecalho_gabarito == '<h1>Novo Gabarito</h1>'
        assert instance.usar_logotipo is True

    def test_meta_fields_inclui_cabecalho_gabarito(self) -> None:
        """Verifica meta fields inclui cabecalho gabarito."""
        fields = ConfiguracaoRelatorioSerializer.Meta.fields
        assert 'cabecalho_gabarito' in fields

    def test_meta_read_only_nao_inclui_cabecalho_gabarito(self) -> None:
        """Verifica meta read only nao inclui cabecalho gabarito."""
        read_only = ConfiguracaoRelatorioSerializer.Meta.read_only_fields
        assert 'cabecalho_gabarito' not in read_only
