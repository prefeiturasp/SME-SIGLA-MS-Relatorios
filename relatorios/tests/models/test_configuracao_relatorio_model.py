"""
Testes unitários para o model ConfiguracaoRelatorio.
"""
import pytest
from relatorios.models import ConfiguracaoRelatorio


pytestmark = pytest.mark.django_db


@pytest.fixture
def configuracao():
    config, _ = ConfiguracaoRelatorio.objects.get_or_create(tipo='LAUDA_VAGAS')
    config.cabecalho = ''
    config.cabecalho_gabarito = ''
    config.texto_final = ''
    config.cabecalho_capa_ata = ''
    config.usar_logotipo = False
    config.save()
    return config


@pytest.fixture
def configuracao_completa():
    config, _ = ConfiguracaoRelatorio.objects.get_or_create(tipo='SUMULA_ESCOLHAS')
    config.usar_logotipo = True
    config.cabecalho = '<h1>Cabeçalho</h1>'
    config.cabecalho_gabarito = '<h1>Gabarito</h1>'
    config.texto_final = '<p>Texto final</p>'
    config.cabecalho_capa_ata = '<h2>Capa</h2>'
    config.save()
    return config


class TestConfiguracaoRelatorioModel:

    def test_criacao_com_defaults(self, configuracao):
        assert configuracao.tipo == 'LAUDA_VAGAS'
        assert configuracao.usar_logotipo is False
        assert configuracao.cabecalho == ''
        assert configuracao.cabecalho_gabarito == ''
        assert configuracao.texto_final == ''
        assert configuracao.cabecalho_capa_ata == ''

    def test_uuid_gerado_automaticamente(self, configuracao):
        assert configuracao.uuid is not None

    def test_timestamps_gerados(self, configuracao):
        assert configuracao.criado_em is not None
        assert configuracao.atualizado_em is not None

    def test_str(self, configuracao):
        assert 'Lauda de Vagas' in str(configuracao)

    def test_tipo_unico(self, configuracao):
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            ConfiguracaoRelatorio.objects.create(tipo=configuracao.tipo)

    def test_ordering_por_tipo(self):
        tipos = list(ConfiguracaoRelatorio.objects.values_list('tipo', flat=True))
        assert tipos == sorted(tipos)

    def test_db_table(self):
        assert ConfiguracaoRelatorio._meta.db_table == 'relatorios_configuracao'


class TestCabecalhoGabarito:

    def test_cabecalho_gabarito_default_vazio(self, configuracao):
        assert configuracao.cabecalho_gabarito == ''

    def test_cabecalho_gabarito_salvo_e_recuperado(self):
        html = '<h1>Cabeçalho Gabarito Teste</h1><p>Linha 2</p>'
        config, _ = ConfiguracaoRelatorio.objects.get_or_create(tipo='LAUDA_CONVOCACAO')
        config.cabecalho_gabarito = html
        config.save()
        config.refresh_from_db()
        assert config.cabecalho_gabarito == html

    def test_cabecalho_gabarito_permite_blank(self):
        config, _ = ConfiguracaoRelatorio.objects.get_or_create(tipo='SUMULA_RECONVOCACAO')
        config.cabecalho_gabarito = ''
        config.save()
        assert config.cabecalho_gabarito == ''

    def test_cabecalho_gabarito_aceita_html_longo(self):
        html_longo = '<div>' + '<p>Linha</p>' * 500 + '</div>'
        config, _ = ConfiguracaoRelatorio.objects.get_or_create(tipo='SUMULA_NAO_ESCOLHAS')
        config.cabecalho_gabarito = html_longo
        config.save()
        config.refresh_from_db()
        assert config.cabecalho_gabarito == html_longo

    def test_cabecalho_gabarito_atualizavel(self, configuracao):
        configuracao.cabecalho_gabarito = '<h2>Novo Gabarito</h2>'
        configuracao.save()
        configuracao.refresh_from_db()
        assert configuracao.cabecalho_gabarito == '<h2>Novo Gabarito</h2>'

    def test_todos_campos_coexistem(self, configuracao_completa):
        assert configuracao_completa.cabecalho == '<h1>Cabeçalho</h1>'
        assert configuracao_completa.cabecalho_gabarito == '<h1>Gabarito</h1>'
        assert configuracao_completa.cabecalho_capa_ata == '<h2>Capa</h2>'
        assert configuracao_completa.texto_final == '<p>Texto final</p>'

    def test_verbose_name_cabecalho_gabarito(self):
        field = ConfiguracaoRelatorio._meta.get_field('cabecalho_gabarito')
        assert field.verbose_name == 'Cabeçalho Gabarito'
