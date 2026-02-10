"""
Testes unitários para o serviço ListagemEscolhasDres.
"""
import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from django.test import RequestFactory
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from datetime import datetime

from relatorios.services.relatorios.listagem_escolhas_dres import ListagemEscolhasDres
from relatorios.models import ConfiguracaoRelatorio, Parametrizacao


pytestmark = pytest.mark.django_db


@pytest.fixture
def configuracao_relatorio():
    """Fixture que cria uma ConfiguracaoRelatorio para testes."""
    return ConfiguracaoRelatorio.objects.get_or_create(
        tipo='LISTAGEM_ESCOLHAS_DRES',
        defaults={
            'usar_logotipo': False,
            'usar_cabecalho_padrao': False,
            'cabecalho': '',
            'texto_final': '',
            'cabecalho_capa_ata': ''
        }
    )[0]


@pytest.fixture
def parametrizacao():
    """Fixture que cria uma Parametrizacao para testes."""
    return Parametrizacao.objects.create(
        cabecalho='Cabeçalho Padrão Teste',
        logo=None
    )


def _make_request():
    """Cria um request mock para os testes."""
    return RequestFactory().get('/relatorios/listagem-escolhas-dres/')


class _MockResponse:
    """Classe auxiliar para mockar respostas HTTP."""
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code
    
    def json(self):
        return self._json_data


@pytest.fixture
def mock_candidatos_response():
    """Fixture com dados mockados de candidatos."""
    return _MockResponse({
        'results': [
            {
                'uuid': 'candidato-uuid-1',
                'classificacao': 1,
                'classificacao_pcd': None,
                'classificacao_nna': 5,
                'inscricao': '12345',
                'candidato': {
                    'nome': 'João Silva',
                    'rg': '123456789',
                    'cpf': '12345678901',
                    'telefone': '11999999999',
                    'registro_funcional': 'RF123'
                }
            },
            {
                'uuid': 'candidato-uuid-2',
                'classificacao': 2,
                'classificacao_pcd': 1,
                'classificacao_nna': None,
                'inscricao': '12346',
                'candidato': {
                    'nome': 'Maria Santos',
                    'rg': '987654321',
                    'cpf': '98765432109',
                    'telefone': '11888888888',
                    'registro_funcional': 'RF456'
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
            'tipo_vaga': 'definitiva',
            'vaga_escola': {
                'cargo_descricao': 'Professor de Educação Infantil',
                'escola': {
                    'nome_oficial': 'EMEF Teste',
                    'codigo_eol': '12345',
                    'tipo_ue': 'EMEF',
                    'dre': {
                        'nome': 'DRE Butantã'
                    }
                }
            }
        },
        {
            'candidato_uuid': 'candidato-uuid-2',
            'tipo_vaga': 'precaria',
            'vaga_escola': {
                'cargo_descricao': 'Professor de Matemática',
                'escola': {
                    'nome_oficial': 'EMEF Teste 2',
                    'codigo_eol': '12346',
                    'tipo_ue': 'EMEF',
                    'dre': {
                        'nome': 'DRE Butantã'
                    }
                }
            }
        }
    ]


@pytest.fixture
def listagem_escolhas_dres_service(settings, configuracao_relatorio, parametrizacao):
    """Fixture que cria uma instância do serviço com mocks."""
    settings.ESCOLHAS_API_URL = 'http://escolhas'
    settings.CANDIDATOS_API_URL = 'http://candidatos'
    settings.RELATORIO_CABECALHO_PADRAO = 'Cabeçalho Padrão'
    
    service = ListagemEscolhasDres(
        configuracao=configuracao_relatorio,
        parametrizacao=parametrizacao
    )
    
    # Mockar os serviços
    service.escolhas_service = Mock()
    service.candidatos_service = Mock()
    
    return service


class TestInit:
    """Testes para o método __init__."""
    
    def test_init(self, settings, configuracao_relatorio, parametrizacao):
        """Testa inicialização."""
        settings.ESCOLHAS_API_URL = 'http://escolhas'
        settings.CANDIDATOS_API_URL = 'http://candidatos'
        
        service = ListagemEscolhasDres(
            configuracao=configuracao_relatorio,
            parametrizacao=parametrizacao,
            extra_param='value'
        )
        
        assert service.escolhas_service is not None
        assert service.candidatos_service is not None


class TestGerar:
    """Testes para o método gerar."""
    
    def test_gerar_html_success(
        self,
        listagem_escolhas_dres_service,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa geração de relatório HTML com sucesso."""
        listagem_escolhas_dres_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        listagem_escolhas_dres_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.listagem_escolhas_dres.render', return_value=HttpResponse('OK')) as m_render:
            response, dados = listagem_escolhas_dres_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='html',
                cabecalho='Cabeçalho Teste'
            )
        
        assert isinstance(response, HttpResponse)
        m_render.assert_called_once()
        assert 'total_escolhas' in dados
        assert dados['total_escolhas'] == 2
    
    def test_gerar_pdf_success(
        self,
        listagem_escolhas_dres_service,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa geração de relatório PDF com sucesso."""
        listagem_escolhas_dres_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        listagem_escolhas_dres_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch.object(listagem_escolhas_dres_service, 'render_to_pdf', return_value=HttpResponse(b'%PDF-1.4', content_type='application/pdf')) as m_pdf:
            response, dados = listagem_escolhas_dres_service.gerar(
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
        listagem_escolhas_dres_service,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa geração de relatório XLS com sucesso."""
        listagem_escolhas_dres_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        listagem_escolhas_dres_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch.object(listagem_escolhas_dres_service, 'render_to_xls', return_value=HttpResponse(b'xlsx', content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')) as m_xls:
            response, dados = listagem_escolhas_dres_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='xls',
                cabecalho='Cabeçalho Teste'
            )
        
        assert isinstance(response, HttpResponse)
        m_xls.assert_called_once()
    
    def test_gerar_docx_success(
        self,
        listagem_escolhas_dres_service,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa geração de relatório DOCX com sucesso (via PDF->DOCX)."""
        listagem_escolhas_dres_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        listagem_escolhas_dres_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response

        mock_pdf2docx = MagicMock()
        with patch.object(listagem_escolhas_dres_service, 'render_to_pdf', return_value=HttpResponse(b'%PDF-1.4', content_type='application/pdf')), \
             patch.dict('sys.modules', {'pdf2docx': mock_pdf2docx}):
            tmp_dir = MagicMock()
            tmp_dir.__enter__ = MagicMock(return_value='/tmp/test')
            tmp_dir.__exit__ = MagicMock(return_value=None)
            m_file = MagicMock()
            m_file.__enter__ = MagicMock(return_value=m_file)
            m_file.__exit__ = MagicMock(return_value=None)
            m_file.read = MagicMock(return_value=b'DOCX')
            with patch('relatorios.services.relatorios.listagem_escolhas_dres.tempfile.TemporaryDirectory', return_value=tmp_dir), \
                 patch('builtins.open', return_value=m_file):
                response, dados = listagem_escolhas_dres_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='docx',
                    cabecalho='Cabeçalho Teste'
                )

        assert isinstance(response, HttpResponse)
        assert 'docx' in response.get('Content-Disposition', '') or 'listagem' in response.get('Content-Disposition', '')
    
    def test_gerar_com_cabecalho_padrao(
        self,
        listagem_escolhas_dres_service,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa que usa cabeçalho padrão quando não fornecido."""
        listagem_escolhas_dres_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        listagem_escolhas_dres_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        listagem_escolhas_dres_service.context['usar_cabecalho_padrao'] = True
        listagem_escolhas_dres_service.context['cabecalho_padrao'] = 'Cabeçalho Padrão'
        
        with patch('relatorios.services.relatorios.listagem_escolhas_dres.render', return_value=HttpResponse('OK')) as m_render:
            response, dados = listagem_escolhas_dres_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='html',
                cabecalho=''
            )
        
        _, args, kwargs = m_render.mock_calls[0]
        context = args[2] if len(args) >= 3 else kwargs.get('context')
        assert context['cabecalho'] == 'Cabeçalho Padrão'
    
    def test_gerar_erro_buscar_candidatos(
        self,
        listagem_escolhas_dres_service
    ):
        """Testa que erro ao buscar candidatos é propagado."""
        listagem_escolhas_dres_service.candidatos_service.buscar_concurso_candidatos_por_processo.side_effect = Exception('Erro API')
        
        with pytest.raises(Exception, match='Erro API'):
            listagem_escolhas_dres_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='html'
            )
    
    def test_gerar_erro_buscar_escolhas(
        self,
        listagem_escolhas_dres_service,
        mock_candidatos_response
    ):
        """Testa que erro ao buscar escolhas é propagado."""
        listagem_escolhas_dres_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        listagem_escolhas_dres_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = Exception('Erro Escolhas')
        
        with pytest.raises(Exception, match='Erro Escolhas'):
            listagem_escolhas_dres_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='html'
            )
    
    def test_gerar_escolha_sem_candidato_uuid(
        self,
        listagem_escolhas_dres_service,
        mock_candidatos_response
    ):
        """Testa que escolhas sem candidato_uuid são ignoradas."""
        listagem_escolhas_dres_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        listagem_escolhas_dres_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = [
            {'candidato_uuid': None},  # Sem candidato
            {'candidato_uuid': 'candidato-uuid-1'}  # Com candidato
        ]
        
        with patch('relatorios.services.relatorios.listagem_escolhas_dres.render', return_value=HttpResponse('OK')):
            response, dados = listagem_escolhas_dres_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='html'
            )
        
        # Deve processar apenas a escolha com candidato
        assert dados['total_escolhas'] == 1
    
    def test_gerar_candidato_nao_encontrado(
        self,
        listagem_escolhas_dres_service,
        mock_candidatos_response
    ):
        """Testa que escolhas com candidato não encontrado são ignoradas."""
        listagem_escolhas_dres_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        listagem_escolhas_dres_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = [
            {
                'candidato_uuid': 'candidato-inexistente',
                'tipo_vaga': 'definitiva',
                'vaga_escola': {}
            }
        ]
        
        with patch('relatorios.services.relatorios.listagem_escolhas_dres.render', return_value=HttpResponse('OK')):
            response, dados = listagem_escolhas_dres_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='html'
            )
        
        # Não deve ter escolhas processadas
        assert dados['total_escolhas'] == 0
    
    def test_gerar_candidatos_lista_direta(
        self,
        listagem_escolhas_dres_service,
        mock_escolhas_response
    ):
        """Testa quando candidatos vem como lista direta (não dict com results)."""
        candidatos_lista = [
            {
                'uuid': 'candidato-uuid-1',
                'classificacao': 1,
                'candidato': {
                    'nome': 'João',
                    'rg': '123',
                    'cpf': '123'
                }
            }
        ]
        
        listagem_escolhas_dres_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = _MockResponse(candidatos_lista)
        listagem_escolhas_dres_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.listagem_escolhas_dres.render', return_value=HttpResponse('OK')):
            response, dados = listagem_escolhas_dres_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='html'
            )
        
        assert isinstance(response, HttpResponse)
    
    def test_gerar_formato_csv(
        self,
        listagem_escolhas_dres_service,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa geração com formato CSV (tratado como XLS)."""
        listagem_escolhas_dres_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        listagem_escolhas_dres_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch.object(listagem_escolhas_dres_service, 'render_to_xls', return_value=HttpResponse(b'xlsx', content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')) as m_xls:
            response, dados = listagem_escolhas_dres_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='csv'
            )
        
        assert isinstance(response, HttpResponse)
        m_xls.assert_called_once()
    
    def test_gerar_formato_xlsx(
        self,
        listagem_escolhas_dres_service,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa geração com formato XLSX."""
        listagem_escolhas_dres_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        listagem_escolhas_dres_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch.object(listagem_escolhas_dres_service, 'render_to_xls', return_value=HttpResponse(b'xlsx', content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')) as m_xls:
            response, dados = listagem_escolhas_dres_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='xlsx'
            )
        
        assert isinstance(response, HttpResponse)
        m_xls.assert_called_once()
    
    def test_gerar_formato_doc(
        self,
        listagem_escolhas_dres_service,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa geração com formato DOC (tratado como DOCX via PDF->DOCX)."""
        listagem_escolhas_dres_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        listagem_escolhas_dres_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response

        mock_pdf2docx = MagicMock()
        with patch.object(listagem_escolhas_dres_service, 'render_to_pdf', return_value=HttpResponse(b'%PDF-1.4', content_type='application/pdf')), \
             patch.dict('sys.modules', {'pdf2docx': mock_pdf2docx}):
            tmp_dir = MagicMock()
            tmp_dir.__enter__ = MagicMock(return_value='/tmp/test')
            tmp_dir.__exit__ = MagicMock(return_value=None)
            m_file = MagicMock()
            m_file.__enter__ = MagicMock(return_value=m_file)
            m_file.__exit__ = MagicMock(return_value=None)
            m_file.read = MagicMock(return_value=b'DOCX')
            with patch('relatorios.services.relatorios.listagem_escolhas_dres.tempfile.TemporaryDirectory', return_value=tmp_dir), \
                 patch('builtins.open', return_value=m_file):
                response, dados = listagem_escolhas_dres_service.gerar(
                    processo_uuid='proc-123',
                    request=_make_request(),
                    formato='doc'
                )

        assert isinstance(response, HttpResponse)
    
    def test_gerar_formato_json(
        self,
        listagem_escolhas_dres_service,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa geração com formato JSON."""
        listagem_escolhas_dres_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        listagem_escolhas_dres_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        response, dados = listagem_escolhas_dres_service.gerar(
            processo_uuid='proc-123',
            request=_make_request(),
            formato='json'
        )
        
        assert isinstance(response, JsonResponse)
        assert dados['total_escolhas'] == 2
    
    def test_gerar_ordenacao_por_cargo(
        self,
        listagem_escolhas_dres_service,
        mock_candidatos_response
    ):
        """Testa ordenação por cargo."""
        escolhas = [
            {
                'candidato_uuid': 'candidato-uuid-1',
                'tipo_vaga': 'definitiva',
                'vaga_escola': {
                    'cargo_descricao': 'Professor B',
                    'escola': {'nome_oficial': 'EMEF 1', 'codigo_eol': '1', 'tipo_ue': 'EMEF', 'dre': {'nome': 'DRE 1'}}
                }
            },
            {
                'candidato_uuid': 'candidato-uuid-1',
                'tipo_vaga': 'definitiva',
                'vaga_escola': {
                    'cargo_descricao': 'Professor A',
                    'escola': {'nome_oficial': 'EMEF 2', 'codigo_eol': '2', 'tipo_ue': 'EMEF', 'dre': {'nome': 'DRE 1'}}
                }
            }
        ]
        
        listagem_escolhas_dres_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        listagem_escolhas_dres_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = escolhas
        
        with patch('relatorios.services.relatorios.listagem_escolhas_dres.render', return_value=HttpResponse('OK')) as m_render:
            response, dados = listagem_escolhas_dres_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='html'
            )
        
        _, args, kwargs = m_render.mock_calls[0]
        context = args[2] if len(args) >= 3 else kwargs.get('context')
        cargos = context['cargos']
        # Verificar que está ordenado por cargo
        assert cargos[0]['descricao'] == 'Professor A'
        assert cargos[1]['descricao'] == 'Professor B'
    
    def test_gerar_dados_vaga_escola_vazios(
        self,
        listagem_escolhas_dres_service,
        mock_candidatos_response
    ):
        """Testa quando vaga_escola está vazio ou None."""
        escolhas = [
            {
                'candidato_uuid': 'candidato-uuid-1',
                'tipo_vaga': 'definitiva',
                'vaga_escola': None  # Vazio
            }
        ]
        
        listagem_escolhas_dres_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        listagem_escolhas_dres_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = escolhas
        
        with patch('relatorios.services.relatorios.listagem_escolhas_dres.render', return_value=HttpResponse('OK')):
            response, dados = listagem_escolhas_dres_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='html'
            )
        
        assert isinstance(response, HttpResponse)
        # Deve processar mesmo com vaga_escola vazio
        assert dados['total_escolhas'] == 1
    
    def test_gerar_tipo_vaga_invalido(
        self,
        listagem_escolhas_dres_service,
        mock_candidatos_response
    ):
        """Testa quando tipo_vaga é inválido."""
        escolhas = [
            {
                'candidato_uuid': 'candidato-uuid-1',
                'tipo_vaga': 'invalido',  # Tipo inválido
                'vaga_escola': {
                    'cargo_descricao': 'Professor',
                    'escola': {'nome_oficial': 'EMEF', 'codigo_eol': '1', 'tipo_ue': 'EMEF', 'dre': {'nome': 'DRE'}}
                }
            }
        ]
        
        listagem_escolhas_dres_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        listagem_escolhas_dres_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = escolhas
        
        with patch('relatorios.services.relatorios.listagem_escolhas_dres.render', return_value=HttpResponse('OK')):
            response, dados = listagem_escolhas_dres_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='html'
            )
        
        # Deve usar '-' para tipo inválido
        escolhas_processadas = dados['escolhas']
        assert escolhas_processadas[0]['tipo_vaga'] == '-'


class TestRenderToXls:
    """Testes para o método render_to_xls."""
    
    def test_render_to_xls_success(self, listagem_escolhas_dres_service):
        """Testa geração de Excel com sucesso."""
        escolhas_list = [
            {
                'cargo': 'Professor',
                'classificacao': 1,
                'classificacao_deficiente': '-',
                'classificacao_nna': 5,
                'rf': 'RF123',
                'rg': '123',
                'cpf': '123',
                'inscricao': '12345',
                'nome': 'João',
                'telefone': '11999999999',
                'dre': 'DRE Butantã',
                'codigo_eol': '12345',
                'tipo_ue': 'EMEF',
                'unidade': 'EMEF Teste',
                'tipo_vaga': 'D'
            }
        ]
        
        context = listagem_escolhas_dres_service.context.copy()
        context['escolhas'] = escolhas_list
        context['cabecalho'] = 'Cabeçalho Teste'
        response = listagem_escolhas_dres_service.render_to_xls(
            context=context,
            filename='test.xlsx'
        )

        assert isinstance(response, HttpResponse)
        assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response['Content-Type']
        assert 'attachment' in response['Content-Disposition']
        assert 'test.xlsx' in response['Content-Disposition']

    def test_render_to_xls_sem_cabecalho(self, listagem_escolhas_dres_service):
        """Testa geração de Excel sem cabeçalho."""
        escolhas_list = []
        
        context = listagem_escolhas_dres_service.context.copy()
        context['escolhas'] = escolhas_list
        context['cabecalho'] = ''
        response = listagem_escolhas_dres_service.render_to_xls(
            context=context,
            filename='test.xlsx'
        )
        
        assert isinstance(response, HttpResponse)
    
    def test_render_to_xls_tipo_vaga_d(self, listagem_escolhas_dres_service):
        """Testa formatação especial para tipo_vaga 'D'."""
        escolhas_list = [
            {
                'cargo': 'Professor',
                'classificacao': 1,
                'classificacao_deficiente': '-',
                'classificacao_nna': '-',
                'rf': '-',
                'rg': '-',
                'cpf': '-',
                'inscricao': '-',
                'nome': 'João',
                'telefone': '-',
                'dre': '-',
                'codigo_eol': '-',
                'tipo_ue': '-',
                'unidade': '-',
                'tipo_vaga': 'D'
            }
        ]
        
        context = listagem_escolhas_dres_service.context.copy()
        context['escolhas'] = escolhas_list
        context['cabecalho'] = 'Cabeçalho'
        response = listagem_escolhas_dres_service.render_to_xls(
            context=context,
            filename='test.xlsx'
        )
        
        assert isinstance(response, HttpResponse)
    
    def test_render_to_xls_tipo_vaga_p(self, listagem_escolhas_dres_service):
        """Testa formatação especial para tipo_vaga 'P'."""
        escolhas_list = [
            {
                'cargo': 'Professor',
                'classificacao': 1,
                'classificacao_deficiente': '-',
                'classificacao_nna': '-',
                'rf': '-',
                'rg': '-',
                'cpf': '-',
                'inscricao': '-',
                'nome': 'João',
                'telefone': '-',
                'dre': '-',
                'codigo_eol': '-',
                'tipo_ue': '-',
                'unidade': '-',
                'tipo_vaga': 'P'
            }
        ]
        
        context = listagem_escolhas_dres_service.context.copy()
        context['escolhas'] = escolhas_list
        context['cabecalho'] = 'Cabeçalho'
        response = listagem_escolhas_dres_service.render_to_xls(
            context=context,
            filename='test.xlsx'
        )
        
        assert isinstance(response, HttpResponse)
    
    def test_render_to_xls_multiplas_escolhas(self, listagem_escolhas_dres_service):
        """Testa geração de Excel com múltiplas escolhas."""
        escolhas_list = [
            {
                'cargo': 'Professor A',
                'classificacao': 1,
                'classificacao_deficiente': '-',
                'classificacao_nna': '-',
                'rf': '-',
                'rg': '-',
                'cpf': '-',
                'inscricao': '-',
                'nome': 'João',
                'telefone': '-',
                'dre': '-',
                'codigo_eol': '-',
                'tipo_ue': '-',
                'unidade': '-',
                'tipo_vaga': 'D'
            },
            {
                'cargo': 'Professor B',
                'classificacao': 2,
                'classificacao_deficiente': '-',
                'classificacao_nna': '-',
                'rf': '-',
                'rg': '-',
                'cpf': '-',
                'inscricao': '-',
                'nome': 'Maria',
                'telefone': '-',
                'dre': '-',
                'codigo_eol': '-',
                'tipo_ue': '-',
                'unidade': '-',
                'tipo_vaga': 'P'
            }
        ]
        
        context = listagem_escolhas_dres_service.context.copy()
        context['escolhas'] = escolhas_list
        context['cabecalho'] = 'Cabeçalho'
        response = listagem_escolhas_dres_service.render_to_xls(
            context=context,
            filename='test.xlsx'
        )
        
        assert isinstance(response, HttpResponse)
    
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.OPENPYXL_AVAILABLE', False)
    def test_render_to_xls_openpyxl_nao_disponivel(self, listagem_escolhas_dres_service):
        """Testa erro quando openpyxl não está disponível."""
        escolhas_list = []
        
        context = listagem_escolhas_dres_service.context.copy()
        context['escolhas'] = escolhas_list
        context['cabecalho'] = 'Cabeçalho'
        with pytest.raises(ImportError, match='openpyxl'):
            listagem_escolhas_dres_service.render_to_xls(
                context=context,
                filename='test.xlsx'
            )
    
    def test_render_to_xls_exception(
        self,
        listagem_escolhas_dres_service
    ):
        """Testa tratamento de exceção no render_to_xls."""
        escolhas_list = []
        
        context = listagem_escolhas_dres_service.context.copy()
        context['escolhas'] = escolhas_list
        context['cabecalho'] = 'Cabeçalho'
        with patch('relatorios.services.relatorios.listagem_escolhas_dres.Workbook', side_effect=Exception('Erro Excel')):
            with pytest.raises(Exception, match='Erro Excel'):
                listagem_escolhas_dres_service.render_to_xls(
                    context=context,
                    filename='test.xlsx'
                )


class TestRenderToDocx:
    """Testes para o método render_to_docx."""
    
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.DOCX_AVAILABLE', False)
    def test_render_to_docx_python_docx_nao_disponivel(self, listagem_escolhas_dres_service):
        """Testa erro quando python-docx não está disponível."""
        escolhas_list = []
        
        with pytest.raises(ImportError, match='python-docx'):
            listagem_escolhas_dres_service.render_to_docx(
                escolhas_list,
                'Cabeçalho',
                'test.docx'
            )
    
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.DOCX_AVAILABLE', True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.Document', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.Inches', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.Pt', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.RGBColor', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.WD_ALIGN_PARAGRAPH', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.qn', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.OxmlElement', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.BytesIO')
    def test_render_to_docx_completo_com_cabecalho(
        self,
        mock_bytesio,
        mock_oxml_element,
        mock_qn,
        mock_wd_align,
        mock_rgb_color,
        mock_pt,
        mock_inches,
        mock_document,
        listagem_escolhas_dres_service
    ):
        """Testa geração completa de Word com cabeçalho e dados."""
        # Setup mocks
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        
        mock_section = MagicMock()
        mock_doc.sections = [mock_section]
        
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_paragraph.add_run.return_value = mock_run
        mock_doc.add_paragraph.return_value = mock_paragraph
        
        mock_table = MagicMock()
        mock_header_row = MagicMock()
        mock_header_cells = []
        for i in range(15):
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
        for i in range(15):
            mock_cell = MagicMock()
            mock_cell.paragraphs = [MagicMock()]
            mock_cell.paragraphs[0].runs = [MagicMock()]
            mock_data_cells.append(mock_cell)
        mock_data_row.cells = mock_data_cells
        mock_table.add_row.return_value = mock_data_row
        mock_doc.add_table.return_value = mock_table
        
        mock_buffer = MagicMock()
        mock_buffer.read.return_value = b'docx content'
        mock_bytesio.return_value = mock_buffer
        
        mock_inches.return_value = MagicMock()
        mock_pt.return_value = MagicMock()
        mock_rgb_color.return_value = MagicMock()
        mock_wd_align.CENTER = 'CENTER'
        mock_wd_align.LEFT = 'LEFT'
        mock_wd_align.RIGHT = 'RIGHT'
        mock_qn.return_value = 'w:shd'
        mock_oxml_element.return_value = MagicMock()
        
        escolhas_list = [
            {
                'cargo': 'Professor',
                'classificacao': 1,
                'classificacao_deficiente': '-',
                'classificacao_nna': 5,
                'rf': 'RF123',
                'rg': '123',
                'cpf': '123',
                'inscricao': '12345',
                'nome': 'João Silva',
                'telefone': '11999999999',
                'dre': 'DRE Butantã',
                'codigo_eol': '12345',
                'tipo_ue': 'EMEF',
                'unidade': 'EMEF Teste',
                'tipo_vaga': 'D'
            }
        ]
        
        response = listagem_escolhas_dres_service.render_to_docx(
            escolhas_list,
            '<b>Cabeçalho Teste</b>',
            'test.docx'
        )
        
        assert isinstance(response, HttpResponse)
        assert 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in response['Content-Type']
        assert 'attachment' in response['Content-Disposition']
        assert 'test.docx' in response['Content-Disposition'] or 'listagem_escolhas_dres.docx' in response['Content-Disposition']
        
        mock_document.assert_called_once()
        mock_doc.save.assert_called_once_with(mock_buffer)
    
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.DOCX_AVAILABLE', True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.Document', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.Inches', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.Pt', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.RGBColor', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.WD_ALIGN_PARAGRAPH', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.qn', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.OxmlElement', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.BytesIO')
    def test_render_to_docx_sem_cabecalho(
        self,
        mock_bytesio,
        mock_oxml_element,
        mock_qn,
        mock_wd_align,
        mock_rgb_color,
        mock_pt,
        mock_inches,
        mock_document,
        listagem_escolhas_dres_service
    ):
        """Testa geração de Word sem cabeçalho."""
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        
        mock_section = MagicMock()
        mock_doc.sections = [mock_section]
        
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_paragraph.add_run.return_value = mock_run
        mock_doc.add_paragraph.return_value = mock_paragraph
        
        mock_table = MagicMock()
        mock_table.rows = [MagicMock()]
        mock_table.rows[0].cells = [MagicMock() for _ in range(15)]
        for cell in mock_table.rows[0].cells:
            cell.paragraphs = [MagicMock()]
            cell.paragraphs[0].runs = [MagicMock()]
            cell._element = MagicMock()
            cell._element.get_or_add_tcPr.return_value = MagicMock()
            cell._element.get_or_add_tcPr.return_value.find.return_value = None
        mock_table.add_row.return_value = MagicMock()
        mock_table.add_row.return_value.cells = [MagicMock() for _ in range(15)]
        for cell in mock_table.add_row.return_value.cells:
            cell.paragraphs = [MagicMock()]
            cell.paragraphs[0].runs = [MagicMock()]
        mock_doc.add_table.return_value = mock_table
        
        mock_buffer = MagicMock()
        mock_buffer.read.return_value = b'docx content'
        mock_bytesio.return_value = mock_buffer
        
        mock_inches.return_value = MagicMock()
        mock_pt.return_value = MagicMock()
        mock_rgb_color.return_value = MagicMock()
        mock_wd_align.CENTER = 'CENTER'
        mock_wd_align.LEFT = 'LEFT'
        mock_wd_align.RIGHT = 'RIGHT'
        mock_qn.return_value = 'w:shd'
        mock_oxml_element.return_value = MagicMock()
        
        escolhas_list = []
        
        response = listagem_escolhas_dres_service.render_to_docx(
            escolhas_list,
            '',
            'test.docx'
        )
        
        assert isinstance(response, HttpResponse)
    
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.DOCX_AVAILABLE', True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.Document', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.Inches', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.Pt', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.RGBColor', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.WD_ALIGN_PARAGRAPH', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.qn', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.OxmlElement', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.BytesIO')
    def test_render_to_docx_tipo_vaga_d(
        self,
        mock_bytesio,
        mock_oxml_element,
        mock_qn,
        mock_wd_align,
        mock_rgb_color,
        mock_pt,
        mock_inches,
        mock_document,
        listagem_escolhas_dres_service
    ):
        """Testa formatação especial para tipo_vaga 'D'."""
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        
        mock_section = MagicMock()
        mock_doc.sections = [mock_section]
        
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_paragraph.add_run.return_value = mock_run
        mock_doc.add_paragraph.return_value = mock_paragraph
        
        mock_table = MagicMock()
        mock_table.rows = [MagicMock()]
        mock_table.rows[0].cells = [MagicMock() for _ in range(15)]
        for cell in mock_table.rows[0].cells:
            cell.paragraphs = [MagicMock()]
            cell.paragraphs[0].runs = [MagicMock()]
            cell._element = MagicMock()
            cell._element.get_or_add_tcPr.return_value = MagicMock()
            cell._element.get_or_add_tcPr.return_value.find.return_value = None
        
        mock_row = MagicMock()
        mock_cells = []
        for i in range(15):
            mock_cell = MagicMock()
            mock_cell.paragraphs = [MagicMock()]
            mock_cell.paragraphs[0].runs = [MagicMock()]
            mock_cells.append(mock_cell)
        mock_row.cells = mock_cells
        mock_table.add_row.return_value = mock_row
        mock_doc.add_table.return_value = mock_table
        
        mock_buffer = MagicMock()
        mock_buffer.read.return_value = b'docx content'
        mock_bytesio.return_value = mock_buffer
        
        mock_inches.return_value = MagicMock()
        mock_pt.return_value = MagicMock()
        mock_rgb_color.return_value = MagicMock()
        mock_wd_align.CENTER = 'CENTER'
        mock_wd_align.LEFT = 'LEFT'
        mock_wd_align.RIGHT = 'RIGHT'
        mock_qn.return_value = 'w:shd'
        mock_oxml_element.return_value = MagicMock()
        
        escolhas_list = [
            {
                'cargo': 'Professor',
                'classificacao': 1,
                'classificacao_deficiente': '-',
                'classificacao_nna': '-',
                'rf': '-',
                'rg': '-',
                'cpf': '-',
                'inscricao': '-',
                'nome': 'João',
                'telefone': '-',
                'dre': '-',
                'codigo_eol': '-',
                'tipo_ue': '-',
                'unidade': '-',
                'tipo_vaga': 'D'
            }
        ]
        
        response = listagem_escolhas_dres_service.render_to_docx(
            escolhas_list,
            'Cabeçalho',
            'test.docx'
        )
        
        assert isinstance(response, HttpResponse)
    
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.DOCX_AVAILABLE', True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.Document', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.Inches', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.Pt', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.RGBColor', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.WD_ALIGN_PARAGRAPH', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.qn', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.OxmlElement', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.BytesIO')
    def test_render_to_docx_tipo_vaga_p(
        self,
        mock_bytesio,
        mock_oxml_element,
        mock_qn,
        mock_wd_align,
        mock_rgb_color,
        mock_pt,
        mock_inches,
        mock_document,
        listagem_escolhas_dres_service
    ):
        """Testa formatação especial para tipo_vaga 'P'."""
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        
        mock_section = MagicMock()
        mock_doc.sections = [mock_section]
        
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_paragraph.add_run.return_value = mock_run
        mock_doc.add_paragraph.return_value = mock_paragraph
        
        mock_table = MagicMock()
        mock_table.rows = [MagicMock()]
        mock_table.rows[0].cells = [MagicMock() for _ in range(15)]
        for cell in mock_table.rows[0].cells:
            cell.paragraphs = [MagicMock()]
            cell.paragraphs[0].runs = [MagicMock()]
            cell._element = MagicMock()
            cell._element.get_or_add_tcPr.return_value = MagicMock()
            cell._element.get_or_add_tcPr.return_value.find.return_value = None
        
        mock_row = MagicMock()
        mock_cells = []
        for i in range(15):
            mock_cell = MagicMock()
            mock_cell.paragraphs = [MagicMock()]
            mock_cell.paragraphs[0].runs = [MagicMock()]
            mock_cells.append(mock_cell)
        mock_row.cells = mock_cells
        mock_table.add_row.return_value = mock_row
        mock_doc.add_table.return_value = mock_table
        
        mock_buffer = MagicMock()
        mock_buffer.read.return_value = b'docx content'
        mock_bytesio.return_value = mock_buffer
        
        mock_inches.return_value = MagicMock()
        mock_pt.return_value = MagicMock()
        mock_rgb_color.return_value = MagicMock()
        mock_wd_align.CENTER = 'CENTER'
        mock_wd_align.LEFT = 'LEFT'
        mock_wd_align.RIGHT = 'RIGHT'
        mock_qn.return_value = 'w:shd'
        mock_oxml_element.return_value = MagicMock()
        
        escolhas_list = [
            {
                'cargo': 'Professor',
                'classificacao': 1,
                'classificacao_deficiente': '-',
                'classificacao_nna': '-',
                'rf': '-',
                'rg': '-',
                'cpf': '-',
                'inscricao': '-',
                'nome': 'João',
                'telefone': '-',
                'dre': '-',
                'codigo_eol': '-',
                'tipo_ue': '-',
                'unidade': '-',
                'tipo_vaga': 'P'
            }
        ]
        
        response = listagem_escolhas_dres_service.render_to_docx(
            escolhas_list,
            'Cabeçalho',
            'test.docx'
        )
        
        assert isinstance(response, HttpResponse)
    
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.DOCX_AVAILABLE', True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.Document', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.Inches', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.Pt', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.RGBColor', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.WD_ALIGN_PARAGRAPH', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.qn', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.OxmlElement', create=True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.BytesIO')
    def test_render_to_docx_com_existing_shd(
        self,
        mock_bytesio,
        mock_oxml_element,
        mock_qn,
        mock_wd_align,
        mock_rgb_color,
        mock_pt,
        mock_inches,
        mock_document,
        listagem_escolhas_dres_service
    ):
        """Testa quando já existe shading element (existing_shd)."""
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        
        mock_section = MagicMock()
        mock_doc.sections = [mock_section]
        
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_paragraph.add_run.return_value = mock_run
        mock_doc.add_paragraph.return_value = mock_paragraph
        
        mock_table = MagicMock()
        mock_header_row = MagicMock()
        mock_header_cells = []
        for i in range(15):
            mock_cell = MagicMock()
            mock_cell.paragraphs = [MagicMock()]
            mock_cell.paragraphs[0].runs = [MagicMock()]
            mock_cell._element = MagicMock()
            mock_tc_pr = MagicMock()
            mock_existing_shd = MagicMock()  # Simula que já existe shading
            mock_tc_pr.find.return_value = mock_existing_shd
            mock_cell._element.get_or_add_tcPr.return_value = mock_tc_pr
            mock_header_cells.append(mock_cell)
        mock_header_row.cells = mock_header_cells
        mock_table.rows = [mock_header_row]
        mock_table.add_row.return_value = MagicMock()
        mock_table.add_row.return_value.cells = [MagicMock() for _ in range(15)]
        for cell in mock_table.add_row.return_value.cells:
            cell.paragraphs = [MagicMock()]
            cell.paragraphs[0].runs = [MagicMock()]
        mock_doc.add_table.return_value = mock_table
        
        mock_buffer = MagicMock()
        mock_buffer.read.return_value = b'docx content'
        mock_bytesio.return_value = mock_buffer
        
        mock_inches.return_value = MagicMock()
        mock_pt.return_value = MagicMock()
        mock_rgb_color.return_value = MagicMock()
        mock_wd_align.CENTER = 'CENTER'
        mock_wd_align.LEFT = 'LEFT'
        mock_wd_align.RIGHT = 'RIGHT'
        mock_qn.return_value = 'w:shd'
        mock_oxml_element.return_value = MagicMock()
        
        escolhas_list = [
            {
                'cargo': 'Professor',
                'classificacao': 1,
                'classificacao_deficiente': '-',
                'classificacao_nna': '-',
                'rf': '-',
                'rg': '-',
                'cpf': '-',
                'inscricao': '-',
                'nome': 'João',
                'telefone': '-',
                'dre': '-',
                'codigo_eol': '-',
                'tipo_ue': '-',
                'unidade': '-',
                'tipo_vaga': 'D'
            }
        ]
        
        response = listagem_escolhas_dres_service.render_to_docx(
            escolhas_list,
            'Cabeçalho',
            'test.docx'
        )
        
        assert isinstance(response, HttpResponse)
        # Verificar que removeu o existing_shd antes de adicionar novo
        for cell in mock_header_cells:
            tc_pr = cell._element.get_or_add_tcPr.return_value
            assert tc_pr.remove.called
    
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.DOCX_AVAILABLE', True)
    @patch('relatorios.services.relatorios.listagem_escolhas_dres.Document')
    def test_render_to_docx_exception(
        self,
        mock_document,
        listagem_escolhas_dres_service
    ):
        """Testa tratamento de exceção no render_to_docx."""
        mock_document.side_effect = Exception('Erro ao criar documento')
        
        escolhas_list = []
        
        with pytest.raises(Exception, match='Erro ao criar documento'):
            listagem_escolhas_dres_service.render_to_docx(
                escolhas_list,
                'Cabeçalho',
                'test.docx'
            )


class TestIntegracaoCompleta:
    """Testes de integração completos."""
    
    def test_fluxo_completo_html(
        self,
        listagem_escolhas_dres_service,
        mock_candidatos_response,
        mock_escolhas_response
    ):
        """Testa fluxo completo de geração HTML."""
        listagem_escolhas_dres_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        listagem_escolhas_dres_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        
        with patch('relatorios.services.relatorios.listagem_escolhas_dres.render', return_value=HttpResponse('OK')) as m_render:
            response, dados = listagem_escolhas_dres_service.gerar(
                processo_uuid='proc-123',
                request=_make_request(),
                formato='html',
                cabecalho='Teste'
            )
        
        assert isinstance(response, HttpResponse)
        m_render.assert_called_once()
        assert isinstance(dados, dict)
        assert 'total_escolhas' in dados
        assert 'escolhas' in dados
