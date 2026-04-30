import pytest
from unittest.mock import patch

from relatorios.models import ConfiguracaoRelatorio, Parametrizacao
from relatorios.services.base.utils import ajustar_logo_caminho
from relatorios.services.factory.relatorio_factory import RelatorioFactory


pytestmark = pytest.mark.django_db


def test_ajustar_logo_caminho_local_returns_same(settings):
    settings.DJANGO_ENVIRONMENT = "local"
    settings.MS_PATH = "/ms-relatorios"
    assert ajustar_logo_caminho("/media/logo.png") == "/media/logo.png"


def test_ajustar_logo_caminho_non_local_prefixes_once(settings):
    settings.DJANGO_ENVIRONMENT = "hom"
    settings.MS_PATH = "/ms-relatorios"
    assert ajustar_logo_caminho("/media/logo.png") == "/ms-relatorios/media/logo.png"
    # não prefixa novamente se já estiver com o segmento
    assert ajustar_logo_caminho("/ms-relatorios/media/logo.png") == "/ms-relatorios/media/logo.png"


def test_ajustar_logo_caminho_invalid_values_return_none():
    assert ajustar_logo_caminho(None) is None
    assert ajustar_logo_caminho(123) is None


def test_relatorio_factory_invalid_type_raises_value_error():
    with patch("relatorios.services.factory.relatorio_factory.ConfiguracaoRelatorio.objects.get") as mock_get:
        with patch("relatorios.services.factory.relatorio_factory.Parametrizacao.objects.first") as mock_first:
            mock_get.return_value = object()
            mock_first.return_value = object()
            with pytest.raises(ValueError, match="não é um relatório válido"):
                RelatorioFactory.obter_relatorio("tipo_invalido")


def test_relatorio_factory_creates_service_for_valid_type():
    ConfiguracaoRelatorio.objects.get_or_create(tipo="LISTA_CANDIDATOS_SESSAO")
    Parametrizacao.objects.get_or_create(cabecalho="cabecalho")

    service = RelatorioFactory.obter_relatorio("LISTA_CANDIDATOS_SESSAO")

    from relatorios.services.relatorios.lista_candidatos_sessao import ListaCandidatosSessao
    assert isinstance(service, ListaCandidatosSessao)
