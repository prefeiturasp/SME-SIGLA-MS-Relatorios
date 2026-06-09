"""Módulo tests/views/test_views_extra."""
from __future__ import annotations
from typing import Any
import uuid
from unittest.mock import Mock, patch
import pytest
from django.http import HttpResponse
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from relatorios.services.ata_escolha_service import CargoObrigatorioError
pytestmark = pytest.mark.django_db

@pytest.fixture
def client() -> Any:
    """Executa client."""
    return APIClient()

def _payload(tipo: Any='LISTA_CANDIDATOS_SESSAO') -> Any:
    """Executa  payload."""
    return {'tipo': tipo, 'usuario': 'u1', 'processo_uuid': str(uuid.uuid4()), 'cabecalho': '<p>x</p>'}

@patch('relatorios.views.relatorios.RelatorioFactory.obter_relatorio')
def test_create_returns_xls_when_query_param_is_xls(mock_factory: Any, client: Any) -> None:
    """Verifica create returns xls when query param is xls."""
    svc = Mock()
    svc.gerar.return_value = (HttpResponse('ok'), {'ok': True})
    mock_factory.return_value = svc
    url = reverse('relatorio-list') + '?formato=xls'
    response = client.post(url, _payload(), format='json')
    assert response.status_code == status.HTTP_200_OK
    assert svc.gerar.call_args.args[2] == 'xls'

@patch('relatorios.views.relatorios.RelatorioFactory.obter_relatorio')
def test_create_returns_pdf_when_query_param_pdf(mock_factory: Any, client: Any) -> None:
    """Verifica create returns pdf when query param pdf."""
    svc = Mock()
    svc.gerar.return_value = (HttpResponse('ok'), {'ok': True})
    mock_factory.return_value = svc
    url = reverse('relatorio-list') + '?formato=pdf'
    response = client.post(url, _payload(), format='json')
    assert response.status_code == status.HTTP_200_OK
    assert svc.gerar.call_args.args[2] == 'pdf'

@patch('relatorios.views.relatorios.RelatorioFactory.obter_relatorio')
def test_create_returns_docx_when_query_param_docx(mock_factory: Any, client: Any) -> None:
    """Verifica create returns docx when query param docx."""
    svc = Mock()
    svc.gerar.return_value = (HttpResponse('ok'), {'ok': True})
    mock_factory.return_value = svc
    url = reverse('relatorio-list') + '?formato=docx'
    response = client.post(url, _payload(), format='json')
    assert response.status_code == status.HTTP_200_OK
    assert svc.gerar.call_args.args[2] == 'docx'

@patch('relatorios.views.relatorios.RelatorioFactory.obter_relatorio')
def test_create_handles_cargo_obrigatorio_error(mock_factory: Any, client: Any) -> None:
    """Verifica create handles cargo obrigatorio error."""
    svc = Mock()
    svc.gerar.side_effect = CargoObrigatorioError(cargos=[{'codigo': '1'}], message='Selecione cargo')
    mock_factory.return_value = svc
    response = client.post(reverse('relatorio-list'), _payload('ATA_ESCOLHA'), format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error'] == 'Selecione cargo'
    assert response.data['cargos'] == [{'codigo': '1'}]

@patch('relatorios.views.relatorios.RelatorioFactory.obter_relatorio', side_effect=ValueError('tipo inválido'))
def test_create_handles_value_error(mock_factory: Any, client: Any) -> None:
    """Verifica create handles value error."""
    response = client.post(reverse('relatorio-list'), _payload(), format='json')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'tipo inválido' in response.data['error']

@patch('relatorios.views.relatorios.RelatorioFactory.obter_relatorio')
def test_create_handles_generic_exception(mock_factory: Any, client: Any) -> None:
    """Verifica create handles generic exception."""
    svc = Mock()
    svc.gerar.side_effect = RuntimeError('falha inesperada')
    mock_factory.return_value = svc
    response = client.post(reverse('relatorio-list'), _payload(), format='json')
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert 'Erro ao gerar relatório' in response.data['error']
