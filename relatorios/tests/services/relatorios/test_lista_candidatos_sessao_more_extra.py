"""Módulo tests/services/relatorios/test_lista_candidatos_sessao_more_extra."""
from __future__ import annotations
from typing import Any
from unittest.mock import patch
import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from relatorios.models import ConfiguracaoRelatorio, Parametrizacao
from relatorios.services.relatorios.lista_candidatos_sessao import ListaCandidatosSessao
pytestmark = pytest.mark.django_db

class _Resp:
    """Define _Resp."""

    def __init__(self, payload: Any, content: Any=b'img') -> None:
        """Executa   init  .
        
        Args:
            self: Instância do objeto.
            payload: Parâmetro payload da operação.
            content: Parâmetro content da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        self._payload = payload
        self.content = content

    def json(self) -> Any:
        """Executa json.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Resultado da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        return self._payload

    def raise_for_status(self) -> Any:
        """Executa raise for status.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Resultado da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        return None

@pytest.fixture
def svc(settings: Any) -> Any:
    """Executa svc.
    
    Args:
        settings: Parâmetro settings da operação.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    settings.CANDIDATOS_API_URL = 'http://candidatos'
    settings.AGENDAS_API_URL = 'http://agendas'
    cfg = ConfiguracaoRelatorio.objects.get_or_create(tipo='LISTA_CANDIDATOS_SESSAO')[0]
    par = Parametrizacao.objects.get_or_create(cabecalho='Cab Padrao')[0]
    return ListaCandidatosSessao(configuracao=cfg, parametrizacao=par)

def test_fetch_candidatos_variants_and_build_context(svc: Any, monkeypatch: Any) -> None:
    """Verifica fetch candidatos variants and build context.
    
    Args:
        svc: Parâmetro svc da operação.
        monkeypatch: Fixture do pytest para substituir objetos.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp({'results': [{'x': 1}]}))
    assert svc._fetch_candidatos(['u1']) == [{'x': 1}]
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp([{'y': 2}]))
    assert svc._fetch_candidatos(['u1']) == [{'y': 2}]
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp('invalid'))
    assert svc._fetch_candidatos(['u1']) == []
    assert svc._fetch_candidatos([]) == []
    ctx = svc._build_context([{'classificacao': 1, 'candidato': {'nome': 'A', 'cpf': '1'}, 'codigo_inscricao': 'X'}], {'sessao': 'S1'})
    assert ctx['agenda']['sessao'] == 'S1'
    assert ctx['candidatos'][0]['nome'] == 'A'

def test_render_xls_and_docx_with_logo_and_sections(svc: Any) -> None:
    """Verifica render xls and docx with logo and sections.
    
    Args:
        svc: Parâmetro svc da operação.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    svc.context['cabecalho'] = 'CAB'
    context = {'usar_logotipo': True, 'logo_url': 'http://img/logo.png', 'texto_final': 'Rodape', 'agendas': [{'agenda': {'escolha_em': '2026-04-01', 'hora_convocacao_inicio': '08:00:00', 'hora_convocacao_fim': '09:00:00', 'sessao': 'S1', 'cargo_nome': 'Professor'}, 'candidatos': [{'classificacao': 1, 'classificacao_nna': None, 'classificacao_pcd': None, 'inscricao': 'I1', 'nome': 'N1', 'cpf': 'C1'}]}, {'agenda': {'sessao': 'S2'}, 'candidatos': []}]}
    with patch('relatorios.services.relatorios.lista_candidatos_sessao.requests.get', return_value=_Resp({})):
        xls = svc._render_xls(context, filename='lista-extra.xlsx')
    docx = svc._render_docx(context, filename='lista-extra.docx')
    assert isinstance(xls, HttpResponse)
    assert isinstance(docx, HttpResponse)
    assert 'lista-extra.xlsx' in xls['Content-Disposition']
    assert 'lista-extra.docx' in docx['Content-Disposition']

def test_gerar_docx_xls_and_exception_path(svc: Any, monkeypatch: Any) -> None:
    """Verifica gerar docx xls and exception path.
    
    Args:
        svc: Parâmetro svc da operação.
        monkeypatch: Fixture do pytest para substituir objetos.
    
    Returns:
        Não retorna valor.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    req = RequestFactory().get('/x')
    monkeypatch.setattr(svc.agendas_service, 'buscar_agendas', lambda **kw: _Resp({'results': [{'retardatario': False, 'candidatos_uuids': ['u1'], 'sessao': 'S'}]}))
    monkeypatch.setattr(svc.candidatos_service, 'buscar_por_uuids', lambda **kw: _Resp({'results': [{'classificacao': 1, 'codigo_inscricao': 'I', 'candidato': {'nome': 'N', 'cpf': 'C'}}]}))
    with patch.object(svc, '_render_xls', return_value=HttpResponse('ok-xls')):
        r_xls, _ = svc.gerar('p1', req, formato='xls')
        assert r_xls.status_code == 200
    with patch.object(svc, '_render_docx', return_value=HttpResponse('ok-docx')):
        r_docx, _ = svc.gerar('p1', req, formato='docx')
        assert r_docx.status_code == 200
    monkeypatch.setattr(svc.agendas_service, 'buscar_agendas', lambda **kw: (_ for _ in ()).throw(RuntimeError('erro agenda')))
    with pytest.raises(RuntimeError):
        svc.gerar('p1', req, formato='html')
