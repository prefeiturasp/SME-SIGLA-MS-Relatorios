import pytest
from unittest.mock import patch, Mock
from django.test import RequestFactory
from django.http import HttpResponse, JsonResponse

from relatorios.services.relatorios.lauda_convocacao import LaudaConvocacao


pytestmark = pytest.mark.django_db


def _make_request():
    return RequestFactory().get('/relatorios/lauda-convocacao/')


def test_gerar_pdf_success(settings):
    settings.CANDIDATOS_API_URL = 'http://candidatos'
    settings.CONVOCACAO_API_URL = 'http://processos'
    settings.AGENDAS_API_URL = 'http://agendas'
    settings.RELATORIO_CABECALHO_PADRAO = 'PADRAO'

    svc = LaudaConvocacao()
    # mockar o service interno para não chamar externas
    svc.lauda_service = Mock()
    svc.lauda_service.processar_lauda_convocacao.return_value = {'cargos': [{'cargo_nome': 'Professor'}]}

    with patch.object(svc, 'render_to_pdf', return_value=HttpResponse(b'%PDF-1.4', content_type='application/pdf')) as m_pdf:
        response, dados = svc.gerar(processo_uuid='abc', request=_make_request(), formato='pdf', cabecalho='CAB')

    m_pdf.assert_called_once()
    assert isinstance(response, HttpResponse)
    assert response['Content-Type'] == 'application/pdf'
    assert dados == {'cargos': [{'cargo_nome': 'Professor'}]}


def test_gerar_html_calls_render_with_context_and_default_header(settings):
    settings.CANDIDATOS_API_URL = 'http://candidatos'
    settings.CONVOCACAO_API_URL = 'http://processos'
    settings.AGENDAS_API_URL = 'http://agendas'
    settings.RELATORIO_CABECALHO_PADRAO = 'HEADER_PADRAO'

    svc = LaudaConvocacao()
    svc.lauda_service = Mock()
    svc.lauda_service.processar_lauda_convocacao.return_value = {'cargos': []}

    with patch('relatorios.services.relatorios.lauda_convocacao.render', return_value=HttpResponse('OK')) as m_render:
        response, dados = svc.gerar(processo_uuid='xyz', request=_make_request(), formato='html', cabecalho='')

    assert isinstance(response, HttpResponse)
    # Verifica que o contexto enviado para render inclui o cabeçalho padrão
    _, args, kwargs = m_render.mock_calls[0]
    context = args[2] if len(args) >= 3 else kwargs.get('context')
    assert context['cabecalho'] == 'HEADER_PADRAO'
    assert context['cabecalho_padrao'] == 'HEADER_PADRAO'
    assert dados == {'cargos': []}


def test_gerar_default_json_success(settings):
    settings.CANDIDATOS_API_URL = 'http://candidatos'
    settings.CONVOCACAO_API_URL = 'http://processos'
    settings.AGENDAS_API_URL = 'http://agendas'
    settings.RELATORIO_CABECALHO_PADRAO = 'PADRAO'

    svc = LaudaConvocacao()
    svc.lauda_service = Mock()
    payload = {'processo_uuid': 'p1', 'cargos': []}
    svc.lauda_service.processar_lauda_convocacao.return_value = payload

    response, dados = svc.gerar(processo_uuid='p1', request=_make_request(), formato='json', cabecalho='qualquer')
    assert isinstance(response, JsonResponse)
    assert dados == payload


def test_gerar_raises_exception_on_service_failure(settings):
    settings.CANDIDATOS_API_URL = 'http://candidatos'
    settings.CONVOCACAO_API_URL = 'http://processos'
    settings.AGENDAS_API_URL = 'http://agendas'
    settings.RELATORIO_CABECALHO_PADRAO = 'PADRAO'

    svc = LaudaConvocacao()
    svc.lauda_service = Mock()
    svc.lauda_service.processar_lauda_convocacao.side_effect = Exception('falha')

    with pytest.raises(Exception):
        svc.gerar(processo_uuid='p1', request=_make_request(), formato='html', cabecalho='')


