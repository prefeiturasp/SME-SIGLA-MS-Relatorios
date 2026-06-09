"""Módulo tests/services/relatorios/test_renderers_heavy_extra."""
from __future__ import annotations
from typing import Any
from unittest.mock import Mock, patch
import pytest
from django.http import HttpResponse, JsonResponse
from relatorios.models import ConfiguracaoRelatorio, Parametrizacao
from relatorios.services.relatorios.lauda_convocacao import LaudaConvocacao
from relatorios.services.relatorios.lauda_vagas import LaudaVagas
from relatorios.services.relatorios.nao_escolhas import SumulaNaoEscolhas
from relatorios.services.relatorios.reconvocacao import SumulaReconvocacao
from relatorios.services.relatorios.relacao_vagas import RelacaoVagas
pytestmark = pytest.mark.django_db

@pytest.fixture
def parametrizacao() -> Any:
    """Executa parametrizacao."""
    return Parametrizacao.objects.get_or_create(cabecalho='CAB PADRAO')[0]

@pytest.fixture
def cfgs() -> Any:
    """Executa cfgs."""
    return {'nao': ConfiguracaoRelatorio.objects.get_or_create(tipo='SUMULA_NAO_ESCOLHAS')[0], 'reco': ConfiguracaoRelatorio.objects.get_or_create(tipo='SUMULA_RECONVOCACAO')[0], 'relacao': ConfiguracaoRelatorio.objects.get_or_create(tipo='RELACAO_VAGAS')[0], 'lauda_vagas': ConfiguracaoRelatorio.objects.get_or_create(tipo='LAUDA_VAGAS')[0], 'lauda_conv': ConfiguracaoRelatorio.objects.get_or_create(tipo='LAUDA_CONVOCACAO')[0]}

def _cargos_candidatos() -> Any:
    """Executa  cargos candidatos."""
    return [{'codigo': '101', 'descricao': 'Professor', 'candidatos': [{'classificacao_geral': 1, 'classificacao_def': '-', 'classificacao_nna': 2, 'nome': 'Maria'}]}]

def _cargos_dres_vagas() -> Any:
    """Executa  cargos dres vagas."""
    return [{'codigo': '101', 'descricao': 'Professor', 'dres': [{'codigo': 'D1', 'nome': 'DRE 1', 'vagas': [{'vagas_definitivas': 2, 'vagas_precarias': 1, 'vagas_definitivas_originais': 2, 'vagas_definitivas_atuais': 1, 'vagas_precarias_originais': 1, 'vagas_precarias_atuais': 1, 'escola': {'tipo_ue': 'EMEF', 'nome_oficial': 'Escola A', 'codigo_eol': '999'}}]}]}]

def _cargos_lauda_conv() -> Any:
    """Executa  cargos lauda conv."""
    return [{'cargo_nome': 'Professor', 'sessoes': [{'numero_sessao': 1, 'horario_formatado': '08:00 às 10:00', 'candidatos': [{'ordem_escolha': 1, 'codigo_inscricao': 'INS1', 'classificacao': 1, 'classificacao_pcd': None, 'classificacao_nna': 2, 'candidato': {'nome': 'Joao'}}]}]}]

def test_sumula_nao_escolhas_renderers(cfgs: Any, parametrizacao: Any) -> None:
    """Verifica sumula nao escolhas renderers."""
    svc = SumulaNaoEscolhas(configuracao=cfgs['nao'], parametrizacao=parametrizacao)
    svc.context.update({'cargos': _cargos_candidatos(), 'texto_final': 'fim'})
    xls = svc.render_to_xls(context=svc.context, filename='nao.xlsx')
    docx = svc.render_to_docx(_cargos_candidatos(), 'cab', 'fim', filename='nao.docx')
    assert isinstance(xls, HttpResponse)
    assert isinstance(docx, HttpResponse)
    assert 'nao.xlsx' in xls['Content-Disposition']
    assert 'nao.docx' in docx['Content-Disposition']

def test_sumula_reconvocacao_renderers(cfgs: Any, parametrizacao: Any) -> None:
    """Verifica sumula reconvocacao renderers."""
    svc = SumulaReconvocacao(configuracao=cfgs['reco'], parametrizacao=parametrizacao)
    svc.context.update({'cargos': _cargos_candidatos(), 'texto_final': 'fim'})
    xls = svc.render_to_xls(context=svc.context, filename='reco.xlsx')
    docx = svc.render_to_docx(_cargos_candidatos(), 'cab', 'fim', filename='reco.docx')
    assert isinstance(xls, HttpResponse)
    assert isinstance(docx, HttpResponse)
    assert 'reco.xlsx' in xls['Content-Disposition']
    assert 'reco.docx' in docx['Content-Disposition']

def test_relacao_vagas_renderers(cfgs: Any, parametrizacao: Any) -> None:
    """Verifica relacao vagas renderers."""
    svc = RelacaoVagas(configuracao=cfgs['relacao'], parametrizacao=parametrizacao)
    svc.context.update({'cargos': _cargos_dres_vagas(), 'texto_final': 'fim'})
    xls = svc.render_to_xls(context=svc.context, filename='relacao.xlsx')
    docx = svc.render_to_docx(_cargos_dres_vagas(), 'cab', 'fim', filename='relacao.docx')
    assert isinstance(xls, HttpResponse)
    assert isinstance(docx, HttpResponse)
    assert 'relacao.xlsx' in xls['Content-Disposition']
    assert 'relacao.docx' in docx['Content-Disposition']

def test_lauda_vagas_renderers(cfgs: Any, parametrizacao: Any) -> None:
    """Verifica lauda vagas renderers."""
    svc = LaudaVagas(configuracao=cfgs['lauda_vagas'], parametrizacao=parametrizacao)
    svc.context.update({'cargos': _cargos_dres_vagas(), 'texto_final': 'fim'})
    xls = svc.render_to_xls(context=svc.context, filename='lauda-vagas.xlsx')
    docx = svc.render_to_docx(_cargos_dres_vagas(), svc.context, 'fim', filename='lauda-vagas.docx')
    assert isinstance(xls, HttpResponse)
    assert isinstance(docx, HttpResponse)
    assert 'lauda-vagas.xlsx' in xls['Content-Disposition']
    assert 'lauda-vagas.docx' in docx['Content-Disposition']

def test_lauda_convocacao_renderers(cfgs: Any, parametrizacao: Any) -> None:
    """Verifica lauda convocacao renderers."""
    svc = LaudaConvocacao(configuracao=cfgs['lauda_conv'], parametrizacao=parametrizacao)
    svc.context.update({'texto_final': 'fim'})
    xls = svc._render_xls(_cargos_lauda_conv(), context=svc.context, filename='lauda-conv.xlsx')
    docx = svc.render_to_docx(_cargos_lauda_conv(), svc.context, 'fim', filename='lauda-conv.docx')
    assert isinstance(xls, HttpResponse)
    assert isinstance(docx, HttpResponse)
    assert 'lauda-conv.xlsx' in xls['Content-Disposition']
    assert 'lauda-conv.docx' in docx['Content-Disposition']

def test_renderers_logo_fetch_error_paths(cfgs: Any, parametrizacao: Any) -> None:
    """Verifica renderers logo fetch error paths."""
    nao = SumulaNaoEscolhas(configuracao=cfgs['nao'], parametrizacao=parametrizacao)
    nao.context.update({'cargos': _cargos_candidatos(), 'usar_logotipo': True, 'logo_url': 'http://x/logo.png'})
    reco = SumulaReconvocacao(configuracao=cfgs['reco'], parametrizacao=parametrizacao)
    reco.context.update({'cargos': _cargos_candidatos(), 'usar_logotipo': True, 'logo_url': 'http://x/logo.png'})
    relacao = RelacaoVagas(configuracao=cfgs['relacao'], parametrizacao=parametrizacao)
    relacao.context.update({'cargos': _cargos_dres_vagas(), 'usar_logotipo': True, 'logo_url': 'http://x/logo.png'})
    lauda_vagas = LaudaVagas(configuracao=cfgs['lauda_vagas'], parametrizacao=parametrizacao)
    lauda_vagas.context.update({'cargos': _cargos_dres_vagas(), 'usar_logotipo': True, 'logo_url': 'http://x/logo.png'})
    lauda_conv = LaudaConvocacao(configuracao=cfgs['lauda_conv'], parametrizacao=parametrizacao)
    lauda_conv.context.update({'usar_logotipo': True, 'logo_url': 'http://x/logo.png'})
    with patch('relatorios.services.relatorios.nao_escolhas.requests.get', side_effect=RuntimeError('img err')):
        nao.render_to_xls(context=nao.context, filename='n.xlsx')
    with patch('relatorios.services.relatorios.reconvocacao.requests.get', side_effect=RuntimeError('img err')):
        reco.render_to_xls(context=reco.context, filename='r.xlsx')
    with patch('relatorios.services.relatorios.relacao_vagas.requests.get', side_effect=RuntimeError('img err')):
        relacao.render_to_xls(context=relacao.context, filename='rv.xlsx')
    with patch('relatorios.services.relatorios.lauda_vagas.requests.get', side_effect=RuntimeError('img err')):
        lauda_vagas.render_to_xls(context=lauda_vagas.context, filename='lv.xlsx')
    with patch('relatorios.services.relatorios.lauda_convocacao.requests.get', side_effect=RuntimeError('img err')):
        lauda_conv._render_xls(_cargos_lauda_conv(), context=lauda_conv.context, filename='lc.xlsx')

def test_gerar_else_json_path_lauda_convocacao(cfgs: Any, parametrizacao: Any) -> None:
    """Verifica gerar else json path lauda convocacao."""
    svc = LaudaConvocacao(configuracao=cfgs['lauda_conv'], parametrizacao=parametrizacao)
    svc.lauda_service = Mock()
    svc.lauda_service.processar_lauda_convocacao.return_value = {'cargos': [], 'processo': 'p1'}
    resp, dados = svc.gerar('p1', Mock(build_absolute_uri=lambda x: x), formato='json')
    assert isinstance(resp, JsonResponse)
    assert dados['processo'] == 'p1'
