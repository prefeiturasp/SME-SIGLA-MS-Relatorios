"""Módulo tests/services/relatorios/test_lauda_convocacao."""
from __future__ import annotations
from typing import Any
from unittest.mock import Mock, patch
import pytest
from django.http import HttpResponse, JsonResponse
from django.test import RequestFactory
from relatorios.models import ConfiguracaoRelatorio, Parametrizacao
from relatorios.services.relatorios.lauda_convocacao import LaudaConvocacao
pytestmark = pytest.mark.django_db

@pytest.fixture
def configuracao_relatorio() -> Any:
    """Fixture que cria uma ConfiguracaoRelatorio para testes.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return ConfiguracaoRelatorio.objects.get_or_create(tipo='LAUDA_CONVOCACAO', defaults={'usar_logotipo': False, 'cabecalho': '', 'texto_final': '', 'cabecalho_capa_ata': ''})[0]

@pytest.fixture
def parametrizacao() -> Any:
    """Fixture que cria uma Parametrizacao para testes.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return Parametrizacao.objects.create(cabecalho='Cabeçalho Padrão Teste', logo=None)

def _make_request() -> Any:
    """Executa  make request.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return RequestFactory().get('/relatorios/lauda-convocacao/')

def test_gerar_pdf_success(settings: Any, configuracao_relatorio: Any, parametrizacao: Any) -> None:
    """Verifica gerar pdf success.
    
    Args:
        settings: Parâmetro settings da operação.
        configuracao_relatorio: Parâmetro configuracao relatorio da operação.
        parametrizacao: Parâmetro parametrizacao da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    settings.CANDIDATOS_API_URL = 'http://candidatos'
    settings.CONVOCACAO_API_URL = 'http://processos'
    settings.AGENDAS_API_URL = 'http://agendas'
    settings.RELATORIO_CABECALHO_PADRAO = 'PADRAO'
    svc = LaudaConvocacao(configuracao=configuracao_relatorio, parametrizacao=parametrizacao)
    svc.lauda_service = Mock()
    svc.lauda_service.processar_lauda_convocacao.return_value = {'cargos': [{'cargo_nome': 'Professor'}]}
    with patch.object(svc, 'render_to_pdf', return_value=HttpResponse(b'%PDF-1.4', content_type='application/pdf')) as m_pdf:
        response, dados = svc.gerar(processo_uuid='abc', request=_make_request(), formato='pdf', cabecalho='CAB')
    m_pdf.assert_called_once()
    assert isinstance(response, HttpResponse)
    assert response['Content-Type'] == 'application/pdf'
    assert dados == {'cargos': [{'cargo_nome': 'Professor'}]}

def test_gerar_html_calls_render_with_context_and_default_header(settings: Any, configuracao_relatorio: Any, parametrizacao: Any) -> None:
    """Verifica gerar html calls render with context and default header.
    
    Args:
        settings: Parâmetro settings da operação.
        configuracao_relatorio: Parâmetro configuracao relatorio da operação.
        parametrizacao: Parâmetro parametrizacao da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    settings.CANDIDATOS_API_URL = 'http://candidatos'
    settings.CONVOCACAO_API_URL = 'http://processos'
    settings.AGENDAS_API_URL = 'http://agendas'
    svc = LaudaConvocacao(configuracao=configuracao_relatorio, parametrizacao=parametrizacao)
    svc.lauda_service = Mock()
    svc.lauda_service.processar_lauda_convocacao.return_value = {'cargos': []}
    with patch('relatorios.services.relatorios.lauda_convocacao.render', return_value=HttpResponse('OK')) as m_render:
        response, dados = svc.gerar(processo_uuid='xyz', request=_make_request(), formato='html', cabecalho='')
    assert isinstance(response, HttpResponse)
    _, args, kwargs = m_render.mock_calls[0]
    context = args[2] if len(args) >= 3 else kwargs.get('context')
    assert context['cabecalho_padrao'] == 'Cabeçalho Padrão Teste'
    assert dados == {'cargos': []}

def test_gerar_default_json_success(settings: Any, configuracao_relatorio: Any, parametrizacao: Any) -> None:
    """Verifica gerar default json success.
    
    Args:
        settings: Parâmetro settings da operação.
        configuracao_relatorio: Parâmetro configuracao relatorio da operação.
        parametrizacao: Parâmetro parametrizacao da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    settings.CANDIDATOS_API_URL = 'http://candidatos'
    settings.CONVOCACAO_API_URL = 'http://processos'
    settings.AGENDAS_API_URL = 'http://agendas'
    settings.RELATORIO_CABECALHO_PADRAO = 'PADRAO'
    svc = LaudaConvocacao(configuracao=configuracao_relatorio, parametrizacao=parametrizacao)
    svc.lauda_service = Mock()
    payload = {'processo_uuid': 'p1', 'cargos': []}
    svc.lauda_service.processar_lauda_convocacao.return_value = payload
    response, dados = svc.gerar(processo_uuid='p1', request=_make_request(), formato='json', cabecalho='qualquer')
    assert isinstance(response, JsonResponse)
    assert dados == payload

def test_gerar_raises_exception_on_service_failure(settings: Any, configuracao_relatorio: Any, parametrizacao: Any) -> None:
    """Verifica gerar raises exception on service failure.
    
    Args:
        settings: Parâmetro settings da operação.
        configuracao_relatorio: Parâmetro configuracao relatorio da operação.
        parametrizacao: Parâmetro parametrizacao da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    settings.CANDIDATOS_API_URL = 'http://candidatos'
    settings.CONVOCACAO_API_URL = 'http://processos'
    settings.AGENDAS_API_URL = 'http://agendas'
    settings.RELATORIO_CABECALHO_PADRAO = 'PADRAO'
    svc = LaudaConvocacao(configuracao=configuracao_relatorio, parametrizacao=parametrizacao)
    svc.lauda_service = Mock()
    svc.lauda_service.processar_lauda_convocacao.side_effect = Exception('falha')
    with pytest.raises(Exception):
        svc.gerar(processo_uuid='p1', request=_make_request(), formato='html', cabecalho='')
