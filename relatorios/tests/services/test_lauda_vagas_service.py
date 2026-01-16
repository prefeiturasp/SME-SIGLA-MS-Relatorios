"""
Testes unitários para o serviço LaudaVagasService.
"""
import sys
from unittest.mock import MagicMock

# Mock render_to_pdf antes de importar
if 'relatorios.utils' not in sys.modules:
    mock_utils = MagicMock()
    mock_utils.render_to_pdf = MagicMock(return_value=MagicMock())
    sys.modules['relatorios.utils'] = mock_utils

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import RequestFactory
from django.http import HttpResponse

from relatorios.services.lauda_vagas_service import LaudaVagasService


pytestmark = pytest.mark.django_db


def _make_request():
    """Cria um request mock para os testes."""
    return RequestFactory().get('/relatorios/lauda-vagas/')


class _MockResponse:
    """Classe auxiliar para mockar respostas HTTP."""
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code
    
    def json(self):
        return self._json_data


@pytest.fixture
def mock_vagas_response():
    """Fixture com dados mockados de vagas."""
    return _MockResponse({
        'vagas': [
            {
                'cargo_codigo': '123',
                'cargo_descricao': 'Professor de Educação Infantil',
                'escola': {
                    'dre': {
                        'codigo': 'DRE001',
                        'nome': 'DRE Butantã'
                    },
                    'nome_oficial': 'EMEF Teste',
                    'codigo_eol': '12345'
                }
            },
            {
                'cargo_codigo': '123',
                'cargo_descricao': 'Professor de Educação Infantil',
                'escola': {
                    'dre': {
                        'codigo': 'DRE001',
                        'nome': 'DRE Butantã'
                    },
                    'nome_oficial': 'EMEF Teste 2',
                    'codigo_eol': '12346'
                }
            },
            {
                'cargo_codigo': '456',
                'cargo_descricao': 'Professor de Matemática',
                'escola': {
                    'dre': {
                        'codigo': 'DRE002',
                        'nome': 'DRE Centro'
                    },
                    'nome_oficial': 'EMEF Centro',
                    'codigo_eol': '12347'
                }
            }
        ]
    })


@pytest.fixture
def lauda_vagas_service(settings):
    """Fixture que cria uma instância do serviço com mocks."""
    settings.ESCOLHAS_API_URL = 'http://escolhas'
    
    service = LaudaVagasService()
    
    # Mockar o serviço
    service.escolhas_service = Mock()
    
    return service


class TestInit:
    """Testes para o método __init__."""
    
    def test_init(self, settings):
        """Testa inicialização."""
        settings.ESCOLHAS_API_URL = 'http://escolhas'
        
        service = LaudaVagasService()
        
        assert service.escolhas_service is not None
        assert service.TEMPLATE_NAME == 'relatorios/vagas_escolas.html'


class TestGerarRelatorio:
    """Testes para o método gerar_relatorio."""
    
    def test_gerar_relatorio_html_success(
        self,
        lauda_vagas_service,
        mock_vagas_response
    ):
        """Testa geração de relatório HTML com sucesso."""
        lauda_vagas_service.escolhas_service.buscar_vagas_escolas.return_value = mock_vagas_response
        
        with patch('relatorios.services.lauda_vagas_service.render', return_value=HttpResponse('OK')) as m_render:
            response = lauda_vagas_service.gerar_relatorio(
                processo_uuid='proc-123',
                request=_make_request()
            )
        
        assert isinstance(response, HttpResponse)
        m_render.assert_called_once()
        lauda_vagas_service.escolhas_service.buscar_vagas_escolas.assert_called_once_with(
            processo_uuid='proc-123'
        )
    
    def test_gerar_relatorio_erro_buscar_vagas(
        self,
        lauda_vagas_service
    ):
        """Testa que erro ao buscar vagas é propagado."""
        lauda_vagas_service.escolhas_service.buscar_vagas_escolas.side_effect = Exception('Erro API')
        
        with pytest.raises(Exception, match='Erro API'):
            lauda_vagas_service.gerar_relatorio(
                processo_uuid='proc-123',
                request=_make_request()
            )
    
    def test_gerar_relatorio_vagas_vazias(
        self,
        lauda_vagas_service
    ):
        """Testa quando não há vagas."""
        lauda_vagas_service.escolhas_service.buscar_vagas_escolas.return_value = _MockResponse({
            'vagas': []
        })
        
        with patch('relatorios.services.lauda_vagas_service.render', return_value=HttpResponse('OK')) as m_render:
            response = lauda_vagas_service.gerar_relatorio(
                processo_uuid='proc-123',
                request=_make_request()
            )
        
        assert isinstance(response, HttpResponse)
        m_render.assert_called_once()
        # Verificar que o contexto tem cargos vazios
        _, args, kwargs = m_render.mock_calls[0]
        context = args[2] if len(args) >= 3 else kwargs.get('context')
        assert context['cargos'] == []
    
    def test_gerar_relatorio_processo_uuid_none(
        self,
        lauda_vagas_service,
        mock_vagas_response
    ):
        """Testa quando processo_uuid é None."""
        lauda_vagas_service.escolhas_service.buscar_vagas_escolas.return_value = mock_vagas_response
        
        with patch('relatorios.services.lauda_vagas_service.render', return_value=HttpResponse('OK')):
            response = lauda_vagas_service.gerar_relatorio(
                processo_uuid=None,
                request=_make_request()
            )
        
        assert isinstance(response, HttpResponse)
        # Verificar que foi chamado com string vazia
        lauda_vagas_service.escolhas_service.buscar_vagas_escolas.assert_called_once_with(
            processo_uuid=''
        )


class TestAgruparVagas:
    """Testes para o método _agrupar_vagas."""
    
    def test_agrupar_vagas_basico(self, lauda_vagas_service):
        """Testa agrupamento básico de vagas."""
        vagas = [
            {
                'cargo_codigo': '123',
                'escola': {
                    'dre': {
                        'codigo': 'DRE001'
                    }
                }
            },
            {
                'cargo_codigo': '123',
                'escola': {
                    'dre': {
                        'codigo': 'DRE001'
                    }
                }
            },
            {
                'cargo_codigo': '456',
                'escola': {
                    'dre': {
                        'codigo': 'DRE002'
                    }
                }
            }
        ]
        
        resultado = lauda_vagas_service._agrupar_vagas(vagas)
        
        assert '123' in resultado
        assert '456' in resultado
        assert 'DRE001' in resultado['123']
        assert 'DRE002' in resultado['456']
        assert len(resultado['123']['DRE001']) == 2
        assert len(resultado['456']['DRE002']) == 1
    
    def test_agrupar_vagas_sem_cargo_codigo(self, lauda_vagas_service):
        """Testa quando vaga não tem cargo_codigo."""
        vagas = [
            {
                'cargo_codigo': None,
                'escola': {
                    'dre': {
                        'codigo': 'DRE001'
                    }
                }
            }
        ]
        
        resultado = lauda_vagas_service._agrupar_vagas(vagas)
        
        assert None in resultado
        assert 'DRE001' in resultado[None]
    
    def test_agrupar_vagas_sem_dre_codigo(self, lauda_vagas_service):
        """Testa quando escola não tem DRE codigo."""
        vagas = [
            {
                'cargo_codigo': '123',
                'escola': {
                    'dre': {
                        'codigo': None
                    }
                }
            }
        ]
        
        resultado = lauda_vagas_service._agrupar_vagas(vagas)
        
        assert '123' in resultado
        assert None in resultado['123']
    
    def test_agrupar_vagas_sem_escola(self, lauda_vagas_service):
        """Testa quando vaga não tem escola."""
        vagas = [
            {
                'cargo_codigo': '123'
                # Sem chave 'escola'
            }
        ]
        
        resultado = lauda_vagas_service._agrupar_vagas(vagas)
        
        # Deve tratar como escola vazia (None)
        assert '123' in resultado
        assert None in resultado['123']
    
    def test_agrupar_vagas_escola_vazia(self, lauda_vagas_service):
        """Testa quando escola está vazia."""
        vagas = [
            {
                'cargo_codigo': '123',
                'escola': {}
            }
        ]
        
        resultado = lauda_vagas_service._agrupar_vagas(vagas)
        
        assert '123' in resultado
        assert None in resultado['123']
    
    def test_agrupar_vagas_dre_vazia(self, lauda_vagas_service):
        """Testa quando DRE está vazia."""
        vagas = [
            {
                'cargo_codigo': '123',
                'escola': {
                    'dre': {}
                }
            }
        ]
        
        resultado = lauda_vagas_service._agrupar_vagas(vagas)
        
        assert '123' in resultado
        assert None in resultado['123']
    
    def test_agrupar_vagas_multiplos_cargos_dres(self, lauda_vagas_service):
        """Testa agrupamento com múltiplos cargos e DREs."""
        vagas = [
            {
                'cargo_codigo': '123',
                'escola': {
                    'dre': {
                        'codigo': 'DRE001'
                    }
                }
            },
            {
                'cargo_codigo': '123',
                'escola': {
                    'dre': {
                        'codigo': 'DRE002'
                    }
                }
            },
            {
                'cargo_codigo': '456',
                'escola': {
                    'dre': {
                        'codigo': 'DRE001'
                    }
                }
            }
        ]
        
        resultado = lauda_vagas_service._agrupar_vagas(vagas)
        
        assert '123' in resultado
        assert '456' in resultado
        assert 'DRE001' in resultado['123']
        assert 'DRE002' in resultado['123']
        assert 'DRE001' in resultado['456']
        assert len(resultado['123']['DRE001']) == 1
        assert len(resultado['123']['DRE002']) == 1
        assert len(resultado['456']['DRE001']) == 1


class TestPrepararDadosTemplate:
    """Testes para o método _preparar_dados_template."""
    
    def test_preparar_dados_template_basico(self, lauda_vagas_service):
        """Testa preparação básica de dados para o template."""
        vagas_agrupadas = {
            '123': {
                'DRE001': [
                    {
                        'cargo_codigo': '123',
                        'cargo_descricao': 'Professor de Educação Infantil',
                        'escola': {
                            'dre': {
                                'codigo': 'DRE001',
                                'nome': 'DRE Butantã'
                            },
                            'nome_oficial': 'EMEF Teste'
                        }
                    }
                ]
            }
        }
        
        resultado = lauda_vagas_service._preparar_dados_template(vagas_agrupadas)
        
        assert len(resultado) == 1
        assert resultado[0]['codigo'] == '123'
        assert resultado[0]['descricao'] == 'Professor de Educação Infantil'
        assert len(resultado[0]['dres']) == 1
        assert resultado[0]['dres'][0]['codigo'] == 'DRE001'
        assert resultado[0]['dres'][0]['nome'] == 'DRE Butantã'
    
    def test_preparar_dados_template_multiplos_cargos(self, lauda_vagas_service):
        """Testa preparação com múltiplos cargos."""
        vagas_agrupadas = {
            '123': {
                'DRE001': [
                    {
                        'cargo_codigo': '123',
                        'cargo_descricao': 'Professor A',
                        'escola': {
                            'dre': {
                                'codigo': 'DRE001',
                                'nome': 'DRE 1'
                            }
                        }
                    }
                ]
            },
            '456': {
                'DRE002': [
                    {
                        'cargo_codigo': '456',
                        'cargo_descricao': 'Professor B',
                        'escola': {
                            'dre': {
                                'codigo': 'DRE002',
                                'nome': 'DRE 2'
                            }
                        }
                    }
                ]
            }
        }
        
        resultado = lauda_vagas_service._preparar_dados_template(vagas_agrupadas)
        
        assert len(resultado) == 2
        assert resultado[0]['codigo'] == '123'
        assert resultado[1]['codigo'] == '456'
    
    def test_preparar_dados_template_multiplas_dres(self, lauda_vagas_service):
        """Testa preparação com múltiplas DREs no mesmo cargo."""
        vagas_agrupadas = {
            '123': {
                'DRE001': [
                    {
                        'cargo_codigo': '123',
                        'cargo_descricao': 'Professor',
                        'escola': {
                            'dre': {
                                'codigo': 'DRE001',
                                'nome': 'DRE 1'
                            }
                        }
                    }
                ],
                'DRE002': [
                    {
                        'cargo_codigo': '123',
                        'cargo_descricao': 'Professor',
                        'escola': {
                            'dre': {
                                'codigo': 'DRE002',
                                'nome': 'DRE 2'
                            }
                        }
                    }
                ]
            }
        }
        
        resultado = lauda_vagas_service._preparar_dados_template(vagas_agrupadas)
        
        assert len(resultado) == 1
        assert len(resultado[0]['dres']) == 2
        assert resultado[0]['dres'][0]['codigo'] == 'DRE001'
        assert resultado[0]['dres'][1]['codigo'] == 'DRE002'
    
    def test_preparar_dados_template_sem_primeira_vaga(self, lauda_vagas_service):
        """Testa quando não há primeira vaga (lista vazia)."""
        vagas_agrupadas = {
            '123': {
                'DRE001': []
            }
        }
        
        resultado = lauda_vagas_service._preparar_dados_template(vagas_agrupadas)
        
        # Não deve adicionar cargo se não há vagas
        assert len(resultado) == 0
    
    def test_preparar_dados_template_sem_cargo_descricao(self, lauda_vagas_service):
        """Testa quando vaga não tem cargo_descricao."""
        vagas_agrupadas = {
            '123': {
                'DRE001': [
                    {
                        'cargo_codigo': '123',
                        'cargo_descricao': '',
                        'escola': {
                            'dre': {
                                'codigo': 'DRE001',
                                'nome': 'DRE 1'
                            }
                        }
                    }
                ]
            }
        }
        
        resultado = lauda_vagas_service._preparar_dados_template(vagas_agrupadas)
        
        assert len(resultado) == 1
        assert resultado[0]['descricao'] == ''
    
    def test_preparar_dados_template_sem_dre_nome(self, lauda_vagas_service):
        """Testa quando DRE não tem nome."""
        vagas_agrupadas = {
            '123': {
                'DRE001': [
                    {
                        'cargo_codigo': '123',
                        'cargo_descricao': 'Professor',
                        'escola': {
                            'dre': {
                                'codigo': 'DRE001',
                                'nome': ''
                            }
                        }
                    }
                ]
            }
        }
        
        resultado = lauda_vagas_service._preparar_dados_template(vagas_agrupadas)
        
        assert len(resultado) == 1
        assert resultado[0]['dres'][0]['nome'] == ''
    
    def test_preparar_dados_template_dre_vazia(self, lauda_vagas_service):
        """Testa quando estrutura de DRE está vazia."""
        vagas_agrupadas = {
            '123': {
                'DRE001': [
                    {
                        'cargo_codigo': '123',
                        'cargo_descricao': 'Professor',
                        'escola': {
                            'dre': {}
                        }
                    }
                ]
            }
        }
        
        resultado = lauda_vagas_service._preparar_dados_template(vagas_agrupadas)
        
        assert len(resultado) == 1
        assert resultado[0]['dres'][0]['nome'] == ''
    
    def test_preparar_dados_template_escola_vazia(self, lauda_vagas_service):
        """Testa quando estrutura de escola está vazia."""
        vagas_agrupadas = {
            '123': {
                'DRE001': [
                    {
                        'cargo_codigo': '123',
                        'cargo_descricao': 'Professor',
                        'escola': {}
                    }
                ]
            }
        }
        
        resultado = lauda_vagas_service._preparar_dados_template(vagas_agrupadas)
        
        assert len(resultado) == 1
        assert resultado[0]['dres'][0]['nome'] == ''
    
    def test_preparar_dados_template_vagas_vazias_em_dre(self, lauda_vagas_service):
        """Testa quando uma DRE tem lista vazia de vagas."""
        vagas_agrupadas = {
            '123': {
                'DRE001': [
                    {
                        'cargo_codigo': '123',
                        'cargo_descricao': 'Professor',
                        'escola': {
                            'dre': {
                                'codigo': 'DRE001',
                                'nome': 'DRE 1'
                            }
                        }
                    }
                ],
                'DRE002': []  # DRE com lista vazia
            }
        }
        
        resultado = lauda_vagas_service._preparar_dados_template(vagas_agrupadas)
        
        # Deve incluir apenas DRE001, ignorando DRE002 vazia
        assert len(resultado) == 1
        assert len(resultado[0]['dres']) == 1
        assert resultado[0]['dres'][0]['codigo'] == 'DRE001'


class TestIntegracaoCompleta:
    """Testes de integração completos."""
    
    def test_fluxo_completo_html(
        self,
        lauda_vagas_service,
        mock_vagas_response
    ):
        """Testa fluxo completo de geração HTML."""
        lauda_vagas_service.escolhas_service.buscar_vagas_escolas.return_value = mock_vagas_response
        
        with patch('relatorios.services.lauda_vagas_service.render', return_value=HttpResponse('OK')) as m_render:
            response = lauda_vagas_service.gerar_relatorio(
                processo_uuid='proc-123',
                request=_make_request()
            )
        
        assert isinstance(response, HttpResponse)
        m_render.assert_called_once()
        
        # Verificar estrutura dos dados
        _, args, kwargs = m_render.mock_calls[0]
        context = args[2] if len(args) >= 3 else kwargs.get('context')
        cargos = context['cargos']
        assert isinstance(cargos, list)
        if len(cargos) > 0:
            assert 'codigo' in cargos[0]
            assert 'descricao' in cargos[0]
            assert 'dres' in cargos[0]
