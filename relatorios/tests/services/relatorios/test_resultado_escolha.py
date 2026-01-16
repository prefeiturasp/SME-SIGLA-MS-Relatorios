"""
Testes unitários para o serviço ResultadoEscolha.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import RequestFactory
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import datetime

from relatorios.services.relatorios.resultado_escolha import ResultadoEscolha


pytestmark = pytest.mark.django_db


def _make_request():
    """Cria um request mock para os testes."""
    return RequestFactory().get('/relatorios/resultado-escolha/')


class _MockResponse:
    """Classe auxiliar para mockar respostas HTTP."""
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code
    
    def json(self):
        return self._json_data


@pytest.fixture
def mock_cargos_response():
    """Fixture com dados mockados de cargos."""
    return _MockResponse([
        {
            'cargo_codigo': '123',
            'cargo_nome': 'Professor de Educação Infantil'
        },
        {
            'codigo_cargo': '456',
            'nome': 'Professor de Matemática'
        }
    ])


@pytest.fixture
def mock_agendas_response():
    """Fixture com dados mockados de agendas."""
    return _MockResponse({
        'results': [
            {
                'uuid': 'agenda-uuid-1',
                'cargo_codigo': '123',
                'cargo_nome': 'Professor de Educação Infantil',
                'candidatos_uuids': ['candidato-uuid-1', 'candidato-uuid-2'],
                'escolha_em': '2026-01-05T10:00:00Z',
                'sessao': 'Sessão 1'
            },
            {
                'uuid': 'agenda-uuid-2',
                'cargo_codigo': '123',
                'cargo_nome': 'Professor de Educação Infantil',
                'candidatos_uuids': ['candidato-uuid-3'],
                'escolha_em': '2026-01-05T14:00:00Z',
                'sessao': 'Sessão 2'
            }
        ]
    })


@pytest.fixture
def mock_candidatos_response():
    """Fixture com dados mockados de candidatos."""
    return _MockResponse({
        'results': [
            {
                'uuid': 'candidato-uuid-1',
                'codigo_cargo': '123',
                'descricao_cargo': 'Professor de Educação Infantil',
                'classificacao': 1,
                'classificacao_pcd': None,
                'classificacao_nna': 5,
                'candidato': {
                    'nome': 'João Silva',
                    'rg': '123456789',
                    'cpf': '12345678901'
                }
            },
            {
                'uuid': 'candidato-uuid-2',
                'codigo_cargo': '123',
                'descricao_cargo': 'Professor de Educação Infantil',
                'classificacao': 2,
                'classificacao_pcd': 1,
                'classificacao_nna': None,
                'candidato': {
                    'nome': 'Maria Santos',
                    'rg': '987654321',
                    'cpf': '98765432109'
                }
            },
            {
                'uuid': 'candidato-uuid-3',
                'codigo_cargo': '123',
                'classificacao': 3,
                'classificacao_pcd': None,
                'classificacao_nna': None,
                'candidato': {
                    'nome': 'Pedro Oliveira',
                    'rg': '111222333',
                    'cpf': '11122233344'
                }
            }
        ]
    })


@pytest.fixture
def mock_escolhas_response():
    """Fixture com dados mockados de escolhas."""
    return [
        {
            'candidato_uuid': 'candidato-uuid-1',
            'tipo_vaga': 'definitiva'
        },
        {
            'candidato_uuid': 'candidato-uuid-2',
            'tipo_vaga': 'precaria'
        },
        {
            'candidato_uuid': 'candidato-uuid-3',
            'tipo_vaga': 'definitiva'
        }
    ]


@pytest.fixture
def resultado_escolha_service(settings):
    """Fixture que cria uma instância do serviço com mocks."""
    settings.ESCOLHAS_API_URL = 'http://escolhas'
    settings.CANDIDATOS_API_URL = 'http://candidatos'
    settings.PROCESSOS_API_URL = 'http://processos'
    settings.AGENDAS_API_URL = 'http://agendas'
    settings.RELATORIO_CABECALHO_PADRAO = 'Cabeçalho Padrão'
    
    service = ResultadoEscolha(tipo='RESULTADO_ESCOLHA_SIM')
    
    # Mockar os serviços
    service.processos_service = Mock()
    service.agendas_service = Mock()
    service.candidatos_service = Mock()
    service.escolhas_service = Mock()
    
    return service


class TestInit:
    """Testes para o método __init__."""
    
    def test_init_com_tipo(self, settings):
        """Testa inicialização com tipo."""
        settings.ESCOLHAS_API_URL = 'http://escolhas'
        settings.CANDIDATOS_API_URL = 'http://candidatos'
        settings.PROCESSOS_API_URL = 'http://processos'
        settings.AGENDAS_API_URL = 'http://agendas'
        
        service = ResultadoEscolha(tipo='RESULTADO_ESCOLHA_SIM', extra_param='value')
        
        assert service.tipo == 'RESULTADO_ESCOLHA_SIM'
        assert service.escolhas_service is not None
        assert service.candidatos_service is not None
        assert service.processos_service is not None
        assert service.agendas_service is not None


class TestExtrairNumeroSessao:
    """Testes para o método _extrair_numero_sessao."""
    
    def test_extrair_numero_sessao_com_sessao_4(self, resultado_escolha_service):
        """Testa extração de número quando vem 'Sessão 4'."""
        resultado = resultado_escolha_service._extrair_numero_sessao('Sessão 4')
        assert resultado == '4'
    
    def test_extrair_numero_sessao_com_sessao_minuscula(self, resultado_escolha_service):
        """Testa extração com 'sessão' em minúscula."""
        resultado = resultado_escolha_service._extrair_numero_sessao('sessão 5')
        assert resultado == '5'
    
    def test_extrair_numero_sessao_apenas_numero(self, resultado_escolha_service):
        """Testa quando já vem apenas o número."""
        resultado = resultado_escolha_service._extrair_numero_sessao('3')
        assert resultado == '3'
    
    def test_extrair_numero_sessao_vazio(self, resultado_escolha_service):
        """Testa quando a sessão está vazia."""
        resultado = resultado_escolha_service._extrair_numero_sessao('')
        assert resultado == '-'
    
    def test_extrair_numero_sessao_hifen(self, resultado_escolha_service):
        """Testa quando a sessão é '-'."""
        resultado = resultado_escolha_service._extrair_numero_sessao('-')
        assert resultado == '-'
    
    def test_extrair_numero_sessao_none(self, resultado_escolha_service):
        """Testa quando a sessão é None."""
        resultado = resultado_escolha_service._extrair_numero_sessao(None)
        assert resultado == '-'
    
    def test_extrair_numero_sessao_com_texto_extra(self, resultado_escolha_service):
        """Testa quando há texto extra além do número."""
        resultado = resultado_escolha_service._extrair_numero_sessao('Sessão 10 - Manhã')
        assert resultado == '10'
    
    def test_extrair_numero_sessao_sem_numero(self, resultado_escolha_service):
        """Testa quando não há número na string."""
        resultado = resultado_escolha_service._extrair_numero_sessao('Sem número')
        assert resultado == 'Sem número'


class TestAgruparPorCargoEAgenda:
    """Testes para o método _agrupar_por_cargo_e_agenda."""
    
    def test_agrupar_por_cargo_e_agenda_basico(self, resultado_escolha_service):
        """Testa agrupamento básico por cargo e agenda."""
        escolhas = [
            {
                'cargo_codigo': '123',
                'cargo_descricao': 'Professor',
                'agenda_uuid': 'agenda-1',
                'agenda_nome': 'Agenda 1',
                'agenda_data': '2026-01-05',
                'agenda_sessao': '1',
                'classificacao_geral': 1,
                'nome': 'João'
            },
            {
                'cargo_codigo': '123',
                'cargo_descricao': 'Professor',
                'agenda_uuid': 'agenda-1',
                'agenda_nome': 'Agenda 1',
                'agenda_data': '2026-01-05',
                'agenda_sessao': '1',
                'classificacao_geral': 2,
                'nome': 'Maria'
            }
        ]
        
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        
        assert len(resultado) == 1
        assert resultado[0]['codigo'] == '123'
        assert resultado[0]['descricao'] == 'Professor'
        assert len(resultado[0]['agendas']) == 1
        assert len(resultado[0]['agendas'][0]['candidatos']) == 2
    
    def test_agrupar_por_cargo_e_agenda_ordenacao_candidatos(self, resultado_escolha_service):
        """Testa que candidatos são ordenados por classificação geral."""
        escolhas = [
            {
                'cargo_codigo': '123',
                'cargo_descricao': 'Professor',
                'agenda_uuid': 'agenda-1',
                'agenda_nome': 'Agenda 1',
                'agenda_data': '2026-01-05',
                'agenda_sessao': '1',
                'classificacao_geral': 3,
                'nome': 'Terceiro'
            },
            {
                'cargo_codigo': '123',
                'cargo_descricao': 'Professor',
                'agenda_uuid': 'agenda-1',
                'agenda_nome': 'Agenda 1',
                'agenda_data': '2026-01-05',
                'agenda_sessao': '1',
                'classificacao_geral': 1,
                'nome': 'Primeiro'
            },
            {
                'cargo_codigo': '123',
                'cargo_descricao': 'Professor',
                'agenda_uuid': 'agenda-1',
                'agenda_nome': 'Agenda 1',
                'agenda_data': '2026-01-05',
                'agenda_sessao': '1',
                'classificacao_geral': 2,
                'nome': 'Segundo'
            }
        ]
        
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        
        candidatos = resultado[0]['agendas'][0]['candidatos']
        assert candidatos[0]['classificacao_geral'] == 1
        assert candidatos[1]['classificacao_geral'] == 2
        assert candidatos[2]['classificacao_geral'] == 3
    
    def test_agrupar_por_cargo_e_agenda_sem_descricao_cargo(self, resultado_escolha_service):
        """Testa quando não há descrição do cargo."""
        escolhas = [
            {
                'cargo_codigo': '123',
                'cargo_descricao': '',
                'agenda_uuid': 'agenda-1',
                'agenda_nome': 'Agenda 1',
                'agenda_data': '2026-01-05',
                'agenda_sessao': '1',
                'classificacao_geral': 1,
                'nome': 'João'
            }
        ]
        
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        
        assert resultado[0]['descricao'] == 'Cargo 123'
    
    def test_agrupar_por_cargo_e_agenda_sem_codigo_cargo(self, resultado_escolha_service):
        """Testa quando não há código do cargo."""
        escolhas = [
            {
                'cargo_codigo': '',
                'cargo_descricao': '',
                'agenda_uuid': 'agenda-1',
                'agenda_nome': 'Agenda 1',
                'agenda_data': '2026-01-05',
                'agenda_sessao': '1',
                'classificacao_geral': 1,
                'nome': 'João'
            }
        ]
        
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        
        assert resultado[0]['descricao'] == 'Cargo não informado'
    
    def test_agrupar_por_cargo_e_agenda_processa_sessao(self, resultado_escolha_service):
        """Testa que a sessão é processada corretamente."""
        escolhas = [
            {
                'cargo_codigo': '123',
                'cargo_descricao': 'Professor',
                'agenda_uuid': 'agenda-1',
                'agenda_nome': 'Agenda 1',
                'agenda_data': '2026-01-05',
                'agenda_sessao': 'Sessão 4',
                'classificacao_geral': 1,
                'nome': 'João'
            }
        ]
        
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        
        assert resultado[0]['agendas'][0]['sessao'] == '4'


class TestGerar:
    """Testes para o método gerar."""
    
    def test_gerar_html_success(
        self, 
        resultado_escolha_service,
        mock_cargos_response,
        mock_agendas_response,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa geração de relatório HTML com sucesso."""
        # Configurar mocks
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')) as m_render:
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html',
                    cabecalho='Cabeçalho Teste'
                )
        
        assert isinstance(response, HttpResponse)
        m_render.assert_called_once()
        assert len(dados) > 0
    
    def test_gerar_pdf_success(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_agendas_response,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa geração de relatório PDF com sucesso."""
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch.object(resultado_escolha_service, 'render_to_pdf', return_value=HttpResponse(b'%PDF-1.4', content_type='application/pdf')) as m_pdf:
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='pdf',
                    cabecalho='Cabeçalho Teste'
                )
        
        assert isinstance(response, HttpResponse)
        assert response['Content-Type'] == 'application/pdf'
        m_pdf.assert_called_once()
    
    def test_gerar_xls_success(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_agendas_response,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa geração de relatório XLS com sucesso."""
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch.object(resultado_escolha_service, 'render_to_xls', return_value=HttpResponse(b'xlsx', content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')) as m_xls:
            response, dados = resultado_escolha_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='xls',
                cabecalho='Cabeçalho Teste'
            )
        
        assert isinstance(response, HttpResponse)
        m_xls.assert_called_once()
    
    def test_gerar_docx_success(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_agendas_response,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa geração de relatório DOCX com sucesso."""
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch.object(resultado_escolha_service, 'render_to_docx', return_value=HttpResponse(b'docx', content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')) as m_docx:
            response, dados = resultado_escolha_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='docx',
                cabecalho='Cabeçalho Teste'
            )
        
        assert isinstance(response, HttpResponse)
        m_docx.assert_called_once()
    
    def test_gerar_com_cabecalho_padrao(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_agendas_response,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa que usa cabeçalho padrão quando não fornecido."""
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')) as m_render:
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html',
                    cabecalho=''
                )
        
        _, args, kwargs = m_render.mock_calls[0]
        context = args[2] if len(args) >= 3 else kwargs.get('context')
        assert context['cabecalho'] == 'Cabeçalho Padrão'
    
    def test_gerar_tipo_reconvocacao(
        self,
        settings,
        mock_cargos_response,
        mock_agendas_response,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa geração com tipo RECONVOCACAO."""
        settings.ESCOLHAS_API_URL = 'http://escolhas'
        settings.CANDIDATOS_API_URL = 'http://candidatos'
        settings.PROCESSOS_API_URL = 'http://processos'
        settings.AGENDAS_API_URL = 'http://agendas'
        settings.RELATORIO_CABECALHO_PADRAO = 'Padrão'
        
        service = ResultadoEscolha(tipo='RESULTADO_ESCOLHA_RECONVOCACAO')
        service.processos_service = Mock()
        service.agendas_service = Mock()
        service.candidatos_service = Mock()
        service.escolhas_service = Mock()
        
        service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        # Verificar que o tipo de escolha foi 'reconvocacao'
        service.escolhas_service.buscar_escolhas_por_candidatos.assert_called_once()
        call_args = service.escolhas_service.buscar_escolhas_por_candidatos.call_args
        assert call_args[1]['situacao'] == 'reconvocacao'
    
    def test_gerar_tipo_nao(
        self,
        settings,
        mock_cargos_response,
        mock_agendas_response,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa geração com tipo NÃO."""
        settings.ESCOLHAS_API_URL = 'http://escolhas'
        settings.CANDIDATOS_API_URL = 'http://candidatos'
        settings.PROCESSOS_API_URL = 'http://processos'
        settings.AGENDAS_API_URL = 'http://agendas'
        settings.RELATORIO_CABECALHO_PADRAO = 'Padrão'
        
        service = ResultadoEscolha(tipo='RESULTADO_ESCOLHA_NAO')
        service.processos_service = Mock()
        service.agendas_service = Mock()
        service.candidatos_service = Mock()
        service.escolhas_service = Mock()
        
        service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        call_args = service.escolhas_service.buscar_escolhas_por_candidatos.call_args
        assert call_args[1]['situacao'] == 'nao-escolha'
    
    def test_gerar_escolha_valor_r(
        self,
        settings,
        mock_cargos_response,
        mock_agendas_response,
        mock_candidatos_response
    ):
        """Testa que escolha valor é 'R' para reconvocação."""
        settings.ESCOLHAS_API_URL = 'http://escolhas'
        settings.CANDIDATOS_API_URL = 'http://candidatos'
        settings.PROCESSOS_API_URL = 'http://processos'
        settings.AGENDAS_API_URL = 'http://agendas'
        settings.RELATORIO_CABECALHO_PADRAO = 'Padrão'
        
        service = ResultadoEscolha(tipo='RESULTADO_ESCOLHA_RECONVOCACAO')
        service.processos_service = Mock()
        service.agendas_service = Mock()
        service.candidatos_service = Mock()
        service.escolhas_service = Mock()
        
        service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        service.escolhas_service.buscar_escolhas_por_candidatos.return_value = [
            {'candidato_uuid': 'candidato-uuid-1'}
        ]
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        # Verificar que a escolha é 'R'
        cargos = dados
        for cargo in cargos:
            for agenda in cargo.get('agendas', []):
                for candidato in agenda.get('candidatos', []):
                    assert candidato.get('escolha') == 'R'
    
    def test_gerar_escolha_valor_n(
        self,
        settings,
        mock_cargos_response,
        mock_agendas_response,
        mock_candidatos_response
    ):
        """Testa que escolha valor é 'N' para não escolha."""
        settings.ESCOLHAS_API_URL = 'http://escolhas'
        settings.CANDIDATOS_API_URL = 'http://candidatos'
        settings.PROCESSOS_API_URL = 'http://processos'
        settings.AGENDAS_API_URL = 'http://agendas'
        settings.RELATORIO_CABECALHO_PADRAO = 'Padrão'
        
        service = ResultadoEscolha(tipo='RESULTADO_ESCOLHA_NAO')
        service.processos_service = Mock()
        service.agendas_service = Mock()
        service.candidatos_service = Mock()
        service.escolhas_service = Mock()
        
        service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        service.escolhas_service.buscar_escolhas_por_candidatos.return_value = [
            {'candidato_uuid': 'candidato-uuid-1'}
        ]
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        # Verificar que a escolha é 'N'
        for cargo in dados:
            for agenda in cargo.get('agendas', []):
                for candidato in agenda.get('candidatos', []):
                    assert candidato.get('escolha') == 'N'
    
    def test_gerar_escolha_valor_s(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_agendas_response,
        mock_candidatos_response
    ):
        """Testa que escolha valor é 'S' para escolha sim."""
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = [
            {'candidato_uuid': 'candidato-uuid-1'}
        ]
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        # Verificar que a escolha é 'S'
        for cargo in dados:
            for agenda in cargo.get('agendas', []):
                for candidato in agenda.get('candidatos', []):
                    assert candidato.get('escolha') == 'S'
    
    def test_gerar_erro_buscar_candidatos(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_agendas_response
    ):
        """Testa que erro ao buscar candidatos é propagado."""
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.side_effect = Exception('Erro API')
        
        with pytest.raises(Exception, match='Erro API'):
            resultado_escolha_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='html'
            )
    
    def test_gerar_erro_buscar_escolhas(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_agendas_response,
        mock_candidatos_response
    ):
        """Testa que erro ao buscar escolhas é propagado."""
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = Exception('Erro Escolhas')
        
        with pytest.raises(Exception, match='Erro Escolhas'):
            resultado_escolha_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='html'
            )
    
    def test_gerar_sem_candidato_na_escolha(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_agendas_response,
        mock_candidatos_response
    ):
        """Testa que escolhas sem candidato_uuid são ignoradas."""
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = [
            {'candidato_uuid': None},  # Sem candidato
            {'candidato_uuid': 'candidato-uuid-1'}  # Com candidato
        ]
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        # Deve processar apenas a escolha com candidato
        total_candidatos = sum(
            len(agenda.get('candidatos', []))
            for cargo in dados
            for agenda in cargo.get('agendas', [])
        )
        assert total_candidatos == 1
    
    def test_gerar_candidato_nao_encontrado(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_agendas_response,
        mock_candidatos_response
    ):
        """Testa que escolhas com candidato não encontrado são ignoradas."""
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = [
            {'candidato_uuid': 'candidato-inexistente'}  # Candidato não está no mapa
        ]
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        # Não deve ter candidatos processados
        total_candidatos = sum(
            len(agenda.get('candidatos', []))
            for cargo in dados
            for agenda in cargo.get('agendas', [])
        )
        assert total_candidatos == 0
    
    def test_gerar_agenda_nao_encontrada_cria_vazia(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_candidatos_response
    ):
        """Testa que quando agenda não é encontrada, cria uma vazia."""
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = _MockResponse({'results': []})
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = [
            {'candidato_uuid': 'candidato-uuid-1'}
        ]
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        # Deve ter criado uma agenda vazia
        assert len(dados) > 0
        assert dados[0]['agendas'][0]['uuid'] is None
    
    def test_gerar_erro_buscar_cargos_continua(
        self,
        resultado_escolha_service,
        mock_agendas_response,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa que erro ao buscar cargos não interrompe o processo."""
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.side_effect = Exception('Erro Cargos')
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        # Deve continuar mesmo com erro ao buscar cargos
        assert isinstance(response, HttpResponse)
    
    def test_gerar_erro_buscar_agendas_continua(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa que erro ao buscar agendas não interrompe o processo."""
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.side_effect = Exception('Erro Agendas')
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        # Deve continuar mesmo com erro ao buscar agendas
        assert isinstance(response, HttpResponse)
    
    def test_gerar_candidatos_lista_direta(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_agendas_response,
        mock_escolhas_response
    ):
        """Testa quando candidatos vem como lista direta (não dict com results)."""
        candidatos_lista = [
            {
                'uuid': 'candidato-uuid-1',
                'codigo_cargo': '123',
                'classificacao': 1,
                'candidato': {
                    'nome': 'João',
                    'rg': '123',
                    'cpf': '123'
                }
            }
        ]
        
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = _MockResponse(candidatos_lista)
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        assert isinstance(response, HttpResponse)
    
    def test_gerar_cargo_descricao_fallback(
        self,
        resultado_escolha_service,
        mock_agendas_response,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa fallback de descrição de cargo quando não encontrada."""
        # Cargos sem descrição
        cargos_response = _MockResponse([
            {
                'cargo_codigo': '123',
                'cargo_nome': ''  # Sem nome
            }
        ])
        
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = _MockResponse({'results': []})
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        assert isinstance(response, HttpResponse)
    
    def test_gerar_cargo_codigo_int(
        self,
        resultado_escolha_service,
        mock_agendas_response,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa quando código do cargo é inteiro."""
        cargos_response = _MockResponse([
            {
                'cargo_codigo': 123,  # Inteiro
                'cargo_nome': 'Professor'
            }
        ])
        
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        assert isinstance(response, HttpResponse)
    
    def test_gerar_candidato_sem_candidato_obj(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_agendas_response,
        mock_escolhas_response
    ):
        """Testa quando candidato não tem objeto candidato."""
        candidatos_response = _MockResponse({
            'results': [
                {
                    'uuid': 'candidato-uuid-1',
                    'codigo_cargo': '123',
                    'classificacao': 1,
                    'candidato': None  # Sem objeto candidato
                }
            ]
        })
        
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        assert isinstance(response, HttpResponse)
    
    def test_gerar_agenda_encontrada_por_cargo(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa quando agenda é encontrada pelo cargo do candidato."""
        # Agenda sem candidatos_uuids, mas com mesmo cargo_codigo
        agenda_response = _MockResponse({
            'results': [
                {
                    'uuid': 'agenda-uuid-1',
                    'cargo_codigo': '123',
                    'cargo_nome': 'Professor',
                    'candidatos_uuids': [],  # Sem candidatos
                    'escolha_em': '2026-01-05',
                    'sessao': '1'
                }
            ]
        })
        
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = agenda_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        assert isinstance(response, HttpResponse)
    
    def test_gerar_formato_csv(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_agendas_response,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa geração com formato CSV (tratado como XLS)."""
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch.object(resultado_escolha_service, 'render_to_xls', return_value=HttpResponse(b'xlsx', content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')) as m_xls:
            response, dados = resultado_escolha_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='csv'
            )
        
        assert isinstance(response, HttpResponse)
        m_xls.assert_called_once()
    
    def test_gerar_formato_doc(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_agendas_response,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa geração com formato DOC (tratado como DOCX)."""
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch.object(resultado_escolha_service, 'render_to_docx', return_value=HttpResponse(b'docx', content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')) as m_docx:
            response, dados = resultado_escolha_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='doc'
            )
        
        assert isinstance(response, HttpResponse)
        m_docx.assert_called_once()
    
    def test_gerar_tipo_invalido(
        self,
        settings,
        mock_cargos_response,
        mock_agendas_response,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa geração com tipo inválido."""
        settings.ESCOLHAS_API_URL = 'http://escolhas'
        settings.CANDIDATOS_API_URL = 'http://candidatos'
        settings.PROCESSOS_API_URL = 'http://processos'
        settings.AGENDAS_API_URL = 'http://agendas'
        settings.RELATORIO_CABECALHO_PADRAO = 'Padrão'
        
        service = ResultadoEscolha(tipo='TIPO_INVALIDO')
        service.processos_service = Mock()
        service.agendas_service = Mock()
        service.candidatos_service = Mock()
        service.escolhas_service = Mock()
        
        service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        # Verificar que a escolha é '-' para tipo inválido
        for cargo in dados:
            for agenda in cargo.get('agendas', []):
                for candidato in agenda.get('candidatos', []):
                    assert candidato.get('escolha') == '-'
    
    def test_gerar_cargo_sem_descricao_sem_codigo(
        self,
        resultado_escolha_service,
        mock_agendas_response,
        mock_escolhas_response
    ):
        """Testa quando candidato não tem descrição nem código de cargo."""
        candidatos_response = _MockResponse({
            'results': [
                {
                    'uuid': 'candidato-uuid-1',
                    'codigo_cargo': '',  # Sem código
                    'descricao_cargo': '',  # Sem descrição
                    'classificacao': 1,
                    'candidato': {
                        'nome': 'João',
                        'rg': '123',
                        'cpf': '123'
                    }
                }
            ]
        })
        
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = _MockResponse([])
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = _MockResponse({'results': []})
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        # Deve ter criado agenda com "Cargo não informado"
        assert len(dados) > 0
        assert dados[0]['descricao'] == 'Cargo não informado'
    
    def test_gerar_agenda_sem_descricao_busca_mapa(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa quando agenda não tem descrição e busca no mapa de cargos."""
        # Agenda sem cargo_nome mas com cargo_codigo
        agenda_response = _MockResponse({
            'results': [
                {
                    'uuid': 'agenda-uuid-1',
                    'cargo_codigo': '123',
                    'cargo_nome': '',  # Sem nome
                    'candidatos_uuids': ['candidato-uuid-1'],
                    'escolha_em': '2026-01-05',
                    'sessao': '1'
                }
            ]
        })
        
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = agenda_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        assert isinstance(response, HttpResponse)
    
    def test_gerar_agenda_sem_descricao_sem_mapa(
        self,
        resultado_escolha_service,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa quando agenda não tem descrição e não encontra no mapa."""
        # Agenda sem cargo_nome e sem cargos no mapa
        agenda_response = _MockResponse({
            'results': [
                {
                    'uuid': 'agenda-uuid-1',
                    'cargo_codigo': '999',  # Código que não está no mapa
                    'cargo_nome': '',  # Sem nome
                    'candidatos_uuids': ['candidato-uuid-1'],
                    'escolha_em': '2026-01-05',
                    'sessao': '1'
                }
            ]
        })
        
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = _MockResponse([])
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = agenda_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        # Deve usar fallback "Cargo 999"
        assert isinstance(response, HttpResponse)
        assert len(dados) > 0
        assert 'Cargo 999' in dados[0]['descricao'] or dados[0]['descricao'] == 'Cargo 999'
    
    def test_gerar_agenda_sem_descricao_sem_codigo(
        self,
        resultado_escolha_service,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa quando agenda não tem descrição nem código."""
        # Agenda sem cargo_nome e sem cargo_codigo
        agenda_response = _MockResponse({
            'results': [
                {
                    'uuid': 'agenda-uuid-1',
                    'cargo_codigo': '',  # Sem código
                    'cargo_nome': '',  # Sem nome
                    'candidatos_uuids': ['candidato-uuid-1'],
                    'escolha_em': '2026-01-05',
                    'sessao': '1'
                }
            ]
        })
        
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = _MockResponse([])
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = agenda_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        # Deve usar fallback "Cargo não informado"
        assert isinstance(response, HttpResponse)
        assert len(dados) > 0
        assert dados[0]['descricao'] == 'Cargo não informado'
    
    def test_render_to_xls_exception(
        self,
        resultado_escolha_service
    ):
        """Testa tratamento de exceção no render_to_xls."""
        cargos_list = [
            {
                'descricao': 'Professor',
                'agendas': []
            }
        ]
        
        with patch('relatorios.services.relatorios.resultado_escolha.Workbook', side_effect=Exception('Erro Excel')):
            with pytest.raises(Exception, match='Erro Excel'):
                resultado_escolha_service.render_to_xls(
                    cargos_list,
                    'Cabeçalho',
                    'test.xlsx'
                )


class TestRenderToXls:
    """Testes para o método render_to_xls."""
    
    def test_render_to_xls_success(self, resultado_escolha_service):
        """Testa geração de Excel com sucesso."""
        cargos_list = [
            {
                'descricao': 'Professor',
                'agendas': [
                    {
                        'sessao': '1',
                        'candidatos': [
                            {
                                'classificacao_geral': 1,
                                'classificacao_nna': 5,
                                'classificacao_def': '-',
                                'nome': 'João',
                                'rg': '123',
                                'cpf': '123',
                                'escolha': 'S'
                            }
                        ]
                    }
                ]
            }
        ]
        
        response = resultado_escolha_service.render_to_xls(
            cargos_list,
            'Cabeçalho Teste',
            'test.xlsx'
        )
        
        assert isinstance(response, HttpResponse)
        assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response['Content-Type']
        assert 'attachment' in response['Content-Disposition']
        assert 'test.xlsx' in response['Content-Disposition']
    
    def test_render_to_xls_sem_cabecalho(self, resultado_escolha_service):
        """Testa geração de Excel sem cabeçalho."""
        cargos_list = [
            {
                'descricao': 'Professor',
                'agendas': []
            }
        ]
        
        response = resultado_escolha_service.render_to_xls(
            cargos_list,
            '',
            'test.xlsx'
        )
        
        assert isinstance(response, HttpResponse)
    
    def test_render_to_xls_multiplos_cargos(self, resultado_escolha_service):
        """Testa geração de Excel com múltiplos cargos."""
        cargos_list = [
            {
                'descricao': 'Professor A',
                'agendas': [
                    {
                        'sessao': '1',
                        'candidatos': [{'classificacao_geral': 1, 'nome': 'João', 'rg': '1', 'cpf': '1', 'escolha': 'S', 'classificacao_nna': '-', 'classificacao_def': '-'}]
                    }
                ]
            },
            {
                'descricao': 'Professor B',
                'agendas': [
                    {
                        'sessao': '2',
                        'candidatos': [{'classificacao_geral': 2, 'nome': 'Maria', 'rg': '2', 'cpf': '2', 'escolha': 'S', 'classificacao_nna': '-', 'classificacao_def': '-'}]
                    }
                ]
            }
        ]
        
        response = resultado_escolha_service.render_to_xls(
            cargos_list,
            'Cabeçalho',
            'test.xlsx'
        )
        
        assert isinstance(response, HttpResponse)
    
    @patch('relatorios.services.relatorios.resultado_escolha.OPENPYXL_AVAILABLE', False)
    def test_render_to_xls_openpyxl_nao_disponivel(self, resultado_escolha_service):
        """Testa erro quando openpyxl não está disponível."""
        cargos_list = []
        
        with pytest.raises(ImportError, match='openpyxl'):
            resultado_escolha_service.render_to_xls(
                cargos_list,
                'Cabeçalho',
                'test.xlsx'
            )


class TestRenderToDocx:
    """Testes para o método render_to_docx."""
    
    @patch('relatorios.services.relatorios.resultado_escolha.DOCX_AVAILABLE', False)
    def test_render_to_docx_python_docx_nao_disponivel(self, resultado_escolha_service):
        """Testa erro quando python-docx não está disponível."""
        cargos_list = []
        
        with pytest.raises(ImportError, match='python-docx'):
            resultado_escolha_service.render_to_docx(
                cargos_list,
                'Cabeçalho',
                'test.docx'
            )
    
    @patch('relatorios.services.relatorios.resultado_escolha.DOCX_AVAILABLE', True)
    @patch('relatorios.services.relatorios.resultado_escolha.Document', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.Inches', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.Pt', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.RGBColor', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.WD_ALIGN_PARAGRAPH', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.qn', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.OxmlElement', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 15, 12, 0, 0))
    @patch('relatorios.services.relatorios.resultado_escolha.BytesIO')
    def test_render_to_docx_completo_com_cabecalho(
        self,
        mock_bytesio,
        mock_timezone,
        mock_oxml_element,
        mock_qn,
        mock_wd_align,
        mock_rgb_color,
        mock_pt,
        mock_inches,
        mock_document,
        resultado_escolha_service
    ):
        """Testa geração completa de Word com cabeçalho e dados."""
        # Setup mocks
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        
        # Mock sections
        mock_section = MagicMock()
        mock_doc.sections = [mock_section]
        
        # Mock paragraphs
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_paragraph.add_run.return_value = mock_run
        mock_paragraph._element = MagicMock()
        mock_paragraph._element.get_or_add_pPr.return_value = MagicMock()
        mock_paragraph._element.get_or_add_pPr.return_value.find.return_value = None
        mock_doc.add_paragraph.return_value = mock_paragraph
        
        # Mock table
        mock_table = MagicMock()
        mock_header_row = MagicMock()
        mock_header_cells = []
        for i in range(8):
            mock_cell = MagicMock()
            mock_cell.paragraphs = [MagicMock()]
            mock_cell.paragraphs[0].runs = [MagicMock()]
            mock_cell._element = MagicMock()
            mock_cell._element.get_or_add_tcPr.return_value = MagicMock()
            mock_cell._element.get_or_add_tcPr.return_value.find.return_value = None
            mock_header_cells.append(mock_cell)
        mock_header_row.cells = mock_header_cells
        mock_table.rows = [mock_header_row]
        
        mock_data_row = MagicMock()
        mock_data_cells = []
        for i in range(8):
            mock_cell = MagicMock()
            mock_cell.paragraphs = [MagicMock()]
            mock_cell.paragraphs[0].runs = [MagicMock()]
            mock_data_cells.append(mock_cell)
        mock_data_row.cells = mock_data_cells
        mock_table.add_row.return_value = mock_data_row
        mock_doc.add_table.return_value = mock_table
        
        # Mock BytesIO
        mock_buffer = MagicMock()
        mock_buffer.read.return_value = b'docx content'
        mock_bytesio.return_value = mock_buffer
        
        # Mock constants
        mock_inches.return_value = MagicMock()
        mock_pt.return_value = MagicMock()
        mock_rgb_color.return_value = MagicMock()
        mock_wd_align.CENTER = 'CENTER'
        mock_wd_align.LEFT = 'LEFT'
        mock_qn.return_value = 'w:shd'
        mock_oxml_element.return_value = MagicMock()
        
        cargos_list = [
            {
                'descricao': 'Professor de Educação Infantil',
                'agendas': [
                    {
                        'sessao': '1',
                        'candidatos': [
                            {
                                'classificacao_geral': 1,
                                'classificacao_nna': 5,
                                'classificacao_def': '-',
                                'nome': 'João Silva',
                                'rg': '123456789',
                                'cpf': '12345678901',
                                'escolha': 'S'
                            }
                        ]
                    }
                ]
            }
        ]
        
        response = resultado_escolha_service.render_to_docx(
            cargos_list,
            '<b>Cabeçalho Teste</b>',
            'test.docx'
        )
        
        assert isinstance(response, HttpResponse)
        assert 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in response['Content-Type']
        assert 'attachment' in response['Content-Disposition']
        assert 'test.docx' in response['Content-Disposition']
        
        # Verificar que Document foi criado
        mock_document.assert_called_once()
        
        # Verificar que margens foram configuradas
        assert mock_section.top_margin is not None
        assert mock_section.bottom_margin is not None
        assert mock_section.left_margin is not None
        assert mock_section.right_margin is not None
        
        # Verificar que parágrafos foram adicionados (cabeçalho, título, data, cargo)
        assert mock_doc.add_paragraph.call_count >= 4
        
        # Verificar que tabela foi criada
        mock_doc.add_table.assert_called_once()
        
        # Verificar que documento foi salvo
        mock_doc.save.assert_called_once_with(mock_buffer)
    
    @patch('relatorios.services.relatorios.resultado_escolha.DOCX_AVAILABLE', True)
    @patch('relatorios.services.relatorios.resultado_escolha.Document', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.Inches', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.Pt', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.RGBColor', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.WD_ALIGN_PARAGRAPH', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.qn', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.OxmlElement', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 12, 25, 12, 0, 0))
    @patch('relatorios.services.relatorios.resultado_escolha.BytesIO')
    def test_render_to_docx_sem_cabecalho(
        self,
        mock_bytesio,
        mock_timezone,
        mock_oxml_element,
        mock_qn,
        mock_wd_align,
        mock_rgb_color,
        mock_pt,
        mock_inches,
        mock_document,
        resultado_escolha_service
    ):
        """Testa geração de Word sem cabeçalho."""
        # Setup mocks
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        
        mock_section = MagicMock()
        mock_doc.sections = [mock_section]
        
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_paragraph.add_run.return_value = mock_run
        mock_paragraph._element = MagicMock()
        mock_paragraph._element.get_or_add_pPr.return_value = MagicMock()
        mock_paragraph._element.get_or_add_pPr.return_value.find.return_value = None
        mock_doc.add_paragraph.return_value = mock_paragraph
        
        mock_table = MagicMock()
        mock_header_row = MagicMock()
        mock_header_cells = []
        for i in range(8):
            mock_cell = MagicMock()
            mock_cell.paragraphs = [MagicMock()]
            mock_cell.paragraphs[0].runs = [MagicMock()]
            mock_cell._element = MagicMock()
            mock_cell._element.get_or_add_tcPr.return_value = MagicMock()
            mock_cell._element.get_or_add_tcPr.return_value.find.return_value = None
            mock_header_cells.append(mock_cell)
        mock_header_row.cells = mock_header_cells
        mock_table.rows = [mock_header_row]
        mock_table.add_row.return_value = MagicMock()
        mock_table.add_row.return_value.cells = [MagicMock() for _ in range(8)]
        for cell in mock_table.add_row.return_value.cells:
            cell.paragraphs = [MagicMock()]
            cell.paragraphs[0].runs = [MagicMock()]
        mock_doc.add_table.return_value = mock_table
        
        mock_buffer = MagicMock()
        mock_buffer.read.return_value = b'docx content'
        mock_bytesio.return_value = mock_buffer
        
        # Mock constants
        mock_inches.return_value = MagicMock()
        mock_pt.return_value = MagicMock()
        mock_rgb_color.return_value = MagicMock()
        mock_wd_align.CENTER = 'CENTER'
        mock_wd_align.LEFT = 'LEFT'
        mock_qn.return_value = 'w:shd'
        mock_oxml_element.return_value = MagicMock()
        
        cargos_list = [
            {
                'descricao': 'Professor',
                'agendas': []
            }
        ]
        
        response = resultado_escolha_service.render_to_docx(
            cargos_list,
            '',  # Sem cabeçalho
            'test.docx'
        )
        
        assert isinstance(response, HttpResponse)
        # Verificar que não foi chamado processar_cabecalho_html (não há cabeçalho)
        # Mas ainda deve ter criado o documento
        mock_document.assert_called_once()
    
    @patch('relatorios.services.relatorios.resultado_escolha.DOCX_AVAILABLE', True)
    @patch('relatorios.services.relatorios.resultado_escolha.Document', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.Inches', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.Pt', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.RGBColor', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.WD_ALIGN_PARAGRAPH', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.qn', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.OxmlElement', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 3, 10, 12, 0, 0))
    @patch('relatorios.services.relatorios.resultado_escolha.BytesIO')
    def test_render_to_docx_multiplos_cargos_e_candidatos(
        self,
        mock_bytesio,
        mock_timezone,
        mock_oxml_element,
        mock_qn,
        mock_wd_align,
        mock_rgb_color,
        mock_pt,
        mock_inches,
        mock_document,
        resultado_escolha_service
    ):
        """Testa geração de Word com múltiplos cargos e candidatos."""
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        
        mock_section = MagicMock()
        mock_doc.sections = [mock_section]
        
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_paragraph.add_run.return_value = mock_run
        mock_paragraph._element = MagicMock()
        mock_paragraph._element.get_or_add_pPr.return_value = MagicMock()
        mock_paragraph._element.get_or_add_pPr.return_value.find.return_value = None
        mock_doc.add_paragraph.return_value = mock_paragraph
        
        # Mock table com múltiplas linhas
        mock_table = MagicMock()
        mock_header_row = MagicMock()
        mock_header_cells = []
        for i in range(8):
            mock_cell = MagicMock()
            mock_cell.paragraphs = [MagicMock()]
            mock_cell.paragraphs[0].runs = [MagicMock()]
            mock_cell._element = MagicMock()
            mock_cell._element.get_or_add_tcPr.return_value = MagicMock()
            mock_cell._element.get_or_add_tcPr.return_value.find.return_value = None
            mock_header_cells.append(mock_cell)
        mock_header_row.cells = mock_header_cells
        mock_table.rows = [mock_header_row]
        
        # Mock para múltiplas linhas de dados
        def create_data_row():
            mock_row = MagicMock()
            mock_cells = []
            for i in range(8):
                mock_cell = MagicMock()
                mock_cell.paragraphs = [MagicMock()]
                mock_cell.paragraphs[0].runs = [MagicMock()]
                mock_cells.append(mock_cell)
            mock_row.cells = mock_cells
            return mock_row
        
        mock_table.add_row.side_effect = lambda: create_data_row()
        mock_doc.add_table.return_value = mock_table
        
        mock_buffer = MagicMock()
        mock_buffer.read.return_value = b'docx content'
        mock_bytesio.return_value = mock_buffer
        
        mock_inches.return_value = MagicMock()
        mock_pt.return_value = MagicMock()
        mock_rgb_color.return_value = MagicMock()
        mock_wd_align.CENTER = 'CENTER'
        mock_wd_align.LEFT = 'LEFT'
        mock_qn.return_value = 'w:shd'
        mock_oxml_element.return_value = MagicMock()
        
        cargos_list = [
            {
                'descricao': 'Professor A',
                'agendas': [
                    {
                        'sessao': '1',
                        'candidatos': [
                            {
                                'classificacao_geral': 1,
                                'classificacao_nna': '-',
                                'classificacao_def': '-',
                                'nome': 'João',
                                'rg': '1',
                                'cpf': '1',
                                'escolha': 'S'
                            },
                            {
                                'classificacao_geral': 2,
                                'classificacao_nna': '-',
                                'classificacao_def': '-',
                                'nome': 'Maria',
                                'rg': '2',
                                'cpf': '2',
                                'escolha': 'S'
                            }
                        ]
                    }
                ]
            },
            {
                'descricao': 'Professor B',
                'agendas': [
                    {
                        'sessao': '2',
                        'candidatos': [
                            {
                                'classificacao_geral': 1,
                                'classificacao_nna': '-',
                                'classificacao_def': '-',
                                'nome': 'Pedro',
                                'rg': '3',
                                'cpf': '3',
                                'escolha': 'N'
                            }
                        ]
                    }
                ]
            }
        ]
        
        response = resultado_escolha_service.render_to_docx(
            cargos_list,
            'Cabeçalho',
            'test.docx'
        )
        
        assert isinstance(response, HttpResponse)
        # Verificar que múltiplas tabelas foram criadas (uma por cargo)
        assert mock_doc.add_table.call_count == 2
    
    @patch('relatorios.services.relatorios.resultado_escolha.DOCX_AVAILABLE', True)
    @patch('relatorios.services.relatorios.resultado_escolha.Document', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.Inches', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.Pt', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.RGBColor', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.WD_ALIGN_PARAGRAPH', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.qn', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.OxmlElement', create=True)
    @patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0))
    @patch('relatorios.services.relatorios.resultado_escolha.BytesIO')
    def test_render_to_docx_com_existing_shd(
        self,
        mock_bytesio,
        mock_timezone,
        mock_oxml_element,
        mock_qn,
        mock_wd_align,
        mock_rgb_color,
        mock_pt,
        mock_inches,
        mock_document,
        resultado_escolha_service
    ):
        """Testa quando já existe shading element (existing_shd)."""
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        
        mock_section = MagicMock()
        mock_doc.sections = [mock_section]
        
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_paragraph.add_run.return_value = mock_run
        mock_paragraph._element = MagicMock()
        mock_p_pr = MagicMock()
        mock_existing_shd = MagicMock()  # Simula que já existe shading
        mock_p_pr.find.return_value = mock_existing_shd
        mock_paragraph._element.get_or_add_pPr.return_value = mock_p_pr
        mock_doc.add_paragraph.return_value = mock_paragraph
        
        mock_table = MagicMock()
        mock_header_row = MagicMock()
        mock_header_cells = []
        for i in range(8):
            mock_cell = MagicMock()
            mock_cell.paragraphs = [MagicMock()]
            mock_cell.paragraphs[0].runs = [MagicMock()]
            mock_cell._element = MagicMock()
            mock_tc_pr = MagicMock()
            mock_existing_shd_cell = MagicMock()  # Simula que já existe shading na célula
            mock_tc_pr.find.return_value = mock_existing_shd_cell
            mock_cell._element.get_or_add_tcPr.return_value = mock_tc_pr
            mock_header_cells.append(mock_cell)
        mock_header_row.cells = mock_header_cells
        mock_table.rows = [mock_header_row]
        mock_table.add_row.return_value = MagicMock()
        mock_table.add_row.return_value.cells = [MagicMock() for _ in range(8)]
        for cell in mock_table.add_row.return_value.cells:
            cell.paragraphs = [MagicMock()]
            cell.paragraphs[0].runs = [MagicMock()]
        mock_doc.add_table.return_value = mock_table
        
        mock_buffer = MagicMock()
        mock_buffer.read.return_value = b'docx content'
        mock_bytesio.return_value = mock_buffer
        
        # Mock constants
        mock_inches.return_value = MagicMock()
        mock_pt.return_value = MagicMock()
        mock_rgb_color.return_value = MagicMock()
        mock_wd_align.CENTER = 'CENTER'
        mock_wd_align.LEFT = 'LEFT'
        mock_qn.return_value = 'w:shd'
        mock_oxml_element.return_value = MagicMock()
        
        cargos_list = [
            {
                'descricao': 'Professor',
                'agendas': [
                    {
                        'sessao': '1',
                        'candidatos': [
                            {
                                'classificacao_geral': 1,
                                'classificacao_nna': '-',
                                'classificacao_def': '-',
                                'nome': 'João',
                                'rg': '1',
                                'cpf': '1',
                                'escolha': 'S'
                            }
                        ]
                    }
                ]
            }
        ]
        
        response = resultado_escolha_service.render_to_docx(
            cargos_list,
            'Cabeçalho',
            'test.docx'
        )
        
        assert isinstance(response, HttpResponse)
        # Verificar que removeu o existing_shd antes de adicionar novo
        assert mock_p_pr.remove.called
    
    @patch('relatorios.services.relatorios.resultado_escolha.DOCX_AVAILABLE', True)
    @patch('relatorios.services.relatorios.resultado_escolha.Document')
    def test_render_to_docx_exception(
        self,
        mock_document,
        resultado_escolha_service
    ):
        """Testa tratamento de exceção no render_to_docx."""
        mock_document.side_effect = Exception('Erro ao criar documento')
        
        cargos_list = [
            {
                'descricao': 'Professor',
                'agendas': []
            }
        ]
        
        with pytest.raises(Exception, match='Erro ao criar documento'):
            resultado_escolha_service.render_to_docx(
                cargos_list,
                'Cabeçalho',
                'test.docx'
            )
    
    def test_agrupar_por_cargo_sem_agenda_uuid(self, resultado_escolha_service):
        """Testa agrupamento quando agenda não tem UUID."""
        escolhas = [
            {
                'cargo_codigo': '123',
                'cargo_descricao': 'Professor',
                'agenda_uuid': None,  # Sem UUID
                'agenda_nome': 'Agenda 1',
                'agenda_data': '2026-01-05',
                'agenda_sessao': '1',
                'classificacao_geral': 1,
                'nome': 'João'
            }
        ]
        
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        
        assert len(resultado) == 1
        assert resultado[0]['codigo'] == '123'
        assert len(resultado[0]['agendas']) == 1
        assert resultado[0]['agendas'][0]['uuid'] is None
    
    def test_agrupar_por_cargo_sessao_nao_numerica(self, resultado_escolha_service):
        """Testa agrupamento quando sessão não é numérica."""
        escolhas = [
            {
                'cargo_codigo': '123',
                'cargo_descricao': 'Professor',
                'agenda_uuid': 'agenda-1',
                'agenda_nome': 'Agenda 1',
                'agenda_data': '2026-01-05',
                'agenda_sessao': 'Especial',  # Sessão não numérica
                'classificacao_geral': 1,
                'nome': 'João'
            }
        ]
        
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        
        assert len(resultado) == 1
        assert resultado[0]['agendas'][0]['sessao'] == 'Especial'
    
    def test_agrupar_por_cargo_classificacao_infinito(self, resultado_escolha_service):
        """Testa ordenação quando classificação não é numérica."""
        escolhas = [
            {
                'cargo_codigo': '123',
                'cargo_descricao': 'Professor',
                'agenda_uuid': 'agenda-1',
                'agenda_nome': 'Agenda 1',
                'agenda_data': '2026-01-05',
                'agenda_sessao': '1',
                'classificacao_geral': '-',  # Não numérico
                'nome': 'João'
            },
            {
                'cargo_codigo': '123',
                'cargo_descricao': 'Professor',
                'agenda_uuid': 'agenda-1',
                'agenda_nome': 'Agenda 1',
                'agenda_data': '2026-01-05',
                'agenda_sessao': '1',
                'classificacao_geral': 1,  # Numérico
                'nome': 'Maria'
            }
        ]
        
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        
        # O candidato com classificação numérica deve vir primeiro
        candidatos = resultado[0]['agendas'][0]['candidatos']
        assert candidatos[0]['classificacao_geral'] == 1
        assert candidatos[1]['classificacao_geral'] == '-'
    
    def test_agrupar_por_cargo_ordenacao_agendas(self, resultado_escolha_service):
        """Testa ordenação de agendas por data e sessão."""
        escolhas = [
            {
                'cargo_codigo': '123',
                'cargo_descricao': 'Professor',
                'agenda_uuid': 'agenda-2',
                'agenda_nome': 'Agenda 2',
                'agenda_data': '2026-01-06',  # Data posterior
                'agenda_sessao': '1',
                'classificacao_geral': 1,
                'nome': 'João'
            },
            {
                'cargo_codigo': '123',
                'cargo_descricao': 'Professor',
                'agenda_uuid': 'agenda-1',
                'agenda_nome': 'Agenda 1',
                'agenda_data': '2026-01-05',  # Data anterior
                'agenda_sessao': '1',
                'classificacao_geral': 1,
                'nome': 'Maria'
            }
        ]
        
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        
        # Agendas devem estar ordenadas por data
        agendas = resultado[0]['agendas']
        assert agendas[0]['data'] == '2026-01-05'
        assert agendas[1]['data'] == '2026-01-06'
    
    def test_agrupar_por_cargo_ordenacao_cargos(self, resultado_escolha_service):
        """Testa ordenação de cargos por descrição."""
        escolhas = [
            {
                'cargo_codigo': '456',
                'cargo_descricao': 'Professor B',
                'agenda_uuid': 'agenda-1',
                'agenda_nome': 'Agenda 1',
                'agenda_data': '2026-01-05',
                'agenda_sessao': '1',
                'classificacao_geral': 1,
                'nome': 'João'
            },
            {
                'cargo_codigo': '123',
                'cargo_descricao': 'Professor A',
                'agenda_uuid': 'agenda-2',
                'agenda_nome': 'Agenda 2',
                'agenda_data': '2026-01-05',
                'agenda_sessao': '1',
                'classificacao_geral': 1,
                'nome': 'Maria'
            }
        ]
        
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        
        # Cargos devem estar ordenados por descrição
        assert resultado[0]['descricao'] == 'Professor A'
        assert resultado[1]['descricao'] == 'Professor B'


class TestIntegracaoCompleta:
    """Testes de integração completos."""
    
    def test_fluxo_completo_html(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_agendas_response,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa fluxo completo de geração HTML."""
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')) as m_render:
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html',
                    cabecalho='Teste'
                )
        
        assert isinstance(response, HttpResponse)
        m_render.assert_called_once()
        
        # Verificar estrutura dos dados
        assert isinstance(dados, list)
        if len(dados) > 0:
            assert 'codigo' in dados[0]
            assert 'descricao' in dados[0]
            assert 'agendas' in dados[0]
    
    def test_fluxo_completo_com_agenda_por_cargo(
        self,
        resultado_escolha_service,
        mock_cargos_response,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa quando agenda é encontrada pelo cargo do candidato."""
        # Agenda sem candidatos_uuids, mas com mesmo cargo_codigo
        agenda_response = _MockResponse({
            'results': [
                {
                    'uuid': 'agenda-uuid-1',
                    'cargo_codigo': '123',
                    'cargo_nome': 'Professor',
                    'candidatos_uuids': [],  # Sem candidatos
                    'escolha_em': '2026-01-05',
                    'sessao': '1'
                }
            ]
        })
        
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = agenda_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='html'
                )
        
        assert isinstance(response, HttpResponse)
        # Deve ter encontrado agenda pelo cargo
        assert len(dados) > 0
