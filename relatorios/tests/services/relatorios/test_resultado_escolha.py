"""Testes unitários para o serviço ResultadoEscolha."""
from __future__ import annotations
from typing import Any
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from relatorios.models import ConfiguracaoRelatorio, Parametrizacao
from relatorios.services.relatorios.resultado_escolha import ResultadoEscolha
pytestmark = pytest.mark.django_db

def _make_request() -> Any:
    """Cria um request mock para os testes.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return RequestFactory().get('/relatorios/resultado-escolha/')

class _MockResponse:
    """Classe auxiliar para mockar respostas HTTP."""

    def __init__(self, json_data: Any, status_code: Any=200) -> None:
        """Executa   init  .
        
        Args:
            self: Instância do objeto.
            json_data: Parâmetro json data da operação.
            status_code: Parâmetro status code da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        self._json_data = json_data
        self.status_code = status_code

    def json(self) -> Any:
        """Executa json.
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Resultado da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        return self._json_data

@pytest.fixture
def mock_cargos_response() -> Any:
    """Fixture com dados mockados de cargos.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return _MockResponse([{'cargo_codigo': '123', 'cargo_nome': 'Professor de Educação Infantil'}, {'codigo_cargo': '456', 'nome': 'Professor de Matemática'}])

@pytest.fixture
def mock_agendas_response() -> Any:
    """Fixture com dados mockados de agendas.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return _MockResponse({'results': [{'uuid': 'agenda-uuid-1', 'cargo_codigo': '123', 'cargo_nome': 'Professor de Educação Infantil', 'candidatos_uuids': ['candidato-uuid-1', 'candidato-uuid-2'], 'escolha_em': '2026-01-05T10:00:00Z', 'sessao': 'Sessão 1'}, {'uuid': 'agenda-uuid-2', 'cargo_codigo': '123', 'cargo_nome': 'Professor de Educação Infantil', 'candidatos_uuids': ['candidato-uuid-3'], 'escolha_em': '2026-01-05T14:00:00Z', 'sessao': 'Sessão 2'}]})

@pytest.fixture
def mock_candidatos_response() -> Any:
    """Fixture com dados mockados de candidatos.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return _MockResponse({'results': [{'uuid': 'candidato-uuid-1', 'codigo_cargo': '123', 'descricao_cargo': 'Professor de Educação Infantil', 'classificacao': 1, 'classificacao_pcd': None, 'classificacao_nna': 5, 'candidato': {'nome': 'João Silva', 'rg': '123456789', 'cpf': '12345678901'}}, {'uuid': 'candidato-uuid-2', 'codigo_cargo': '123', 'descricao_cargo': 'Professor de Educação Infantil', 'classificacao': 2, 'classificacao_pcd': 1, 'classificacao_nna': None, 'candidato': {'nome': 'Maria Santos', 'rg': '987654321', 'cpf': '98765432109'}}, {'uuid': 'candidato-uuid-3', 'codigo_cargo': '123', 'classificacao': 3, 'classificacao_pcd': None, 'classificacao_nna': None, 'candidato': {'nome': 'Pedro Oliveira', 'rg': '111222333', 'cpf': '11122233344'}}]})

@pytest.fixture
def mock_escolhas_response() -> Any:
    """Fixture com dados mockados de escolhas.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return [{'candidato_uuid': 'candidato-uuid-1', 'tipo_vaga': 'definitiva'}, {'candidato_uuid': 'candidato-uuid-2', 'tipo_vaga': 'precaria'}, {'candidato_uuid': 'candidato-uuid-3', 'tipo_vaga': 'definitiva'}]

@pytest.fixture
def configuracao_relatorio() -> Any:
    """Fixture que cria ou atualiza uma ConfiguracaoRelatorio para testes.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    configuracao, _ = ConfiguracaoRelatorio.objects.update_or_create(tipo='RESULTADO_ESCOLHA', defaults={'usar_logotipo': False, 'cabecalho': 'Cabeçalho Teste', 'texto_final': 'Texto Final Teste', 'cabecalho_capa_ata': ''})
    return configuracao

@pytest.fixture
def parametrizacao() -> Any:
    """Fixture que cria uma Parametrizacao para testes.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return Parametrizacao.objects.create(cabecalho='Cabeçalho Padrão Teste', logo=None)

@pytest.fixture
def resultado_escolha_service(settings: Any, configuracao_relatorio: Any, parametrizacao: Any) -> Any:
    """Fixture que cria uma instância do serviço com mocks.
    
    Args:
        settings: Parâmetro settings da operação.
        configuracao_relatorio: Parâmetro configuracao relatorio da operação.
        parametrizacao: Parâmetro parametrizacao da operação.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    settings.ESCOLHAS_API_URL = 'http://escolhas'
    settings.CANDIDATOS_API_URL = 'http://candidatos'
    settings.PROCESSOS_API_URL = 'http://processos'
    settings.AGENDAS_API_URL = 'http://agendas'
    settings.RELATORIO_CABECALHO_PADRAO = 'Cabeçalho Padrão'
    service = ResultadoEscolha(tipo='RESULTADO_ESCOLHA', configuracao=configuracao_relatorio, parametrizacao=parametrizacao)
    service.processos_service = Mock()
    service.agendas_service = Mock()
    service.candidatos_service = Mock()
    service.escolhas_service = Mock()
    return service

class TestInit:
    """Testes para o método __init__."""

    def test_init_com_tipo(self, settings: Any, configuracao_relatorio: Any, parametrizacao: Any) -> None:
        """Testa inicialização com tipo.
        
        Args:
            self: Instância do objeto.
            settings: Parâmetro settings da operação.
            configuracao_relatorio: Parâmetro configuracao relatorio da operação.
            parametrizacao: Parâmetro parametrizacao da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        settings.ESCOLHAS_API_URL = 'http://escolhas'
        settings.CANDIDATOS_API_URL = 'http://candidatos'
        settings.PROCESSOS_API_URL = 'http://processos'
        settings.AGENDAS_API_URL = 'http://agendas'
        service = ResultadoEscolha(tipo='RESULTADO_ESCOLHA', configuracao=configuracao_relatorio, parametrizacao=parametrizacao, extra_param='value')
        assert service.tipo == 'RESULTADO_ESCOLHA'
        assert service.escolhas_service is not None
        assert service.candidatos_service is not None
        assert service.processos_service is not None
        assert service.agendas_service is not None
        assert service.context is not None
        assert 'cabecalho' in service.context
        assert 'texto_final' in service.context

class TestExtrairNumeroSessao:
    """Testes para o método _extrair_numero_sessao."""

    def test_extrair_numero_sessao_com_sessao_4(self, resultado_escolha_service: Any) -> None:
        """Testa extração de número quando vem 'Sessão 4'.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado = resultado_escolha_service._extrair_numero_sessao('Sessão 4')
        assert resultado == '4'

    def test_extrair_numero_sessao_com_sessao_minuscula(self, resultado_escolha_service: Any) -> None:
        """Testa extração com 'sessão' em minúscula.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado = resultado_escolha_service._extrair_numero_sessao('sessão 5')
        assert resultado == '5'

    def test_extrair_numero_sessao_apenas_numero(self, resultado_escolha_service: Any) -> None:
        """Testa quando já vem apenas o número.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado = resultado_escolha_service._extrair_numero_sessao('3')
        assert resultado == '3'

    def test_extrair_numero_sessao_vazio(self, resultado_escolha_service: Any) -> None:
        """Testa quando a sessão está vazia.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado = resultado_escolha_service._extrair_numero_sessao('')
        assert resultado == '-'

    def test_extrair_numero_sessao_hifen(self, resultado_escolha_service: Any) -> None:
        """Testa quando a sessão é '-'.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado = resultado_escolha_service._extrair_numero_sessao('-')
        assert resultado == '-'

    def test_extrair_numero_sessao_none(self, resultado_escolha_service: Any) -> None:
        """Testa quando a sessão é None.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado = resultado_escolha_service._extrair_numero_sessao(None)
        assert resultado == '-'

    def test_extrair_numero_sessao_com_texto_extra(self, resultado_escolha_service: Any) -> None:
        """Testa quando há texto extra além do número.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado = resultado_escolha_service._extrair_numero_sessao('Sessão 10 - Manhã')
        assert resultado == '10'

    def test_extrair_numero_sessao_sem_numero(self, resultado_escolha_service: Any) -> None:
        """Testa quando não há número na string.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado = resultado_escolha_service._extrair_numero_sessao('Sem número')
        assert resultado == 'Sem número'

class TestAgruparPorCargoEAgenda:
    """Testes para o método _agrupar_por_cargo_e_agenda."""

    def test_agrupar_por_cargo_e_agenda_basico(self, resultado_escolha_service: Any) -> None:
        """Testa agrupamento básico por cargo e agenda.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        escolhas = [{'cargo_codigo': '123', 'cargo_descricao': 'Professor', 'agenda_uuid': 'agenda-1', 'agenda_nome': 'Agenda 1', 'agenda_data': '2026-01-05', 'agenda_sessao': '1', 'classificacao_geral': 1, 'nome': 'João'}, {'cargo_codigo': '123', 'cargo_descricao': 'Professor', 'agenda_uuid': 'agenda-1', 'agenda_nome': 'Agenda 1', 'agenda_data': '2026-01-05', 'agenda_sessao': '1', 'classificacao_geral': 2, 'nome': 'Maria'}]
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        assert len(resultado) == 1
        assert resultado[0]['codigo'] == '123'
        assert resultado[0]['descricao'] == 'Professor'
        assert len(resultado[0]['agendas']) == 1
        assert len(resultado[0]['agendas'][0]['candidatos']) == 2

    def test_agrupar_por_cargo_e_agenda_ordenacao_candidatos(self, resultado_escolha_service: Any) -> None:
        """Testa que candidatos são ordenados por classificação geral.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        escolhas = [{'cargo_codigo': '123', 'cargo_descricao': 'Professor', 'agenda_uuid': 'agenda-1', 'agenda_nome': 'Agenda 1', 'agenda_data': '2026-01-05', 'agenda_sessao': '1', 'classificacao_geral': 3, 'nome': 'Terceiro'}, {'cargo_codigo': '123', 'cargo_descricao': 'Professor', 'agenda_uuid': 'agenda-1', 'agenda_nome': 'Agenda 1', 'agenda_data': '2026-01-05', 'agenda_sessao': '1', 'classificacao_geral': 1, 'nome': 'Primeiro'}, {'cargo_codigo': '123', 'cargo_descricao': 'Professor', 'agenda_uuid': 'agenda-1', 'agenda_nome': 'Agenda 1', 'agenda_data': '2026-01-05', 'agenda_sessao': '1', 'classificacao_geral': 2, 'nome': 'Segundo'}]
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        candidatos = resultado[0]['agendas'][0]['candidatos']
        assert candidatos[0]['classificacao_geral'] == 1
        assert candidatos[1]['classificacao_geral'] == 2
        assert candidatos[2]['classificacao_geral'] == 3

    def test_agrupar_por_cargo_e_agenda_sem_descricao_cargo(self, resultado_escolha_service: Any) -> None:
        """Testa quando não há descrição do cargo.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        escolhas = [{'cargo_codigo': '123', 'cargo_descricao': '', 'agenda_uuid': 'agenda-1', 'agenda_nome': 'Agenda 1', 'agenda_data': '2026-01-05', 'agenda_sessao': '1', 'classificacao_geral': 1, 'nome': 'João'}]
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        assert resultado[0]['descricao'] == 'Cargo 123'

    def test_agrupar_por_cargo_e_agenda_sem_codigo_cargo(self, resultado_escolha_service: Any) -> None:
        """Testa quando não há código do cargo.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        escolhas = [{'cargo_codigo': '', 'cargo_descricao': '', 'agenda_uuid': 'agenda-1', 'agenda_nome': 'Agenda 1', 'agenda_data': '2026-01-05', 'agenda_sessao': '1', 'classificacao_geral': 1, 'nome': 'João'}]
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        assert resultado[0]['descricao'] == 'Cargo não informado'

    def test_agrupar_por_cargo_e_agenda_processa_sessao(self, resultado_escolha_service: Any) -> None:
        """Testa que a sessão é processada corretamente.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        escolhas = [{'cargo_codigo': '123', 'cargo_descricao': 'Professor', 'agenda_uuid': 'agenda-1', 'agenda_nome': 'Agenda 1', 'agenda_data': '2026-01-05', 'agenda_sessao': 'Sessão 4', 'classificacao_geral': 1, 'nome': 'João'}]
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        assert resultado[0]['agendas'][0]['sessao'] == '4'

class TestGerar:
    """Testes para o método gerar."""

    def test_gerar_html_success(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa geração de relatório HTML com sucesso.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')) as m_render:
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html', cabecalho='Cabeçalho Teste')
        assert isinstance(response, HttpResponse)
        m_render.assert_called_once()
        assert len(dados) > 0

    def test_gerar_pdf_success(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa geração de relatório PDF com sucesso.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        with patch.object(resultado_escolha_service, 'render_to_pdf', return_value=HttpResponse(b'%PDF-1.4', content_type='application/pdf')) as m_pdf:
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='pdf', cabecalho='Cabeçalho Teste')
        assert isinstance(response, HttpResponse)
        assert response['Content-Type'] == 'application/pdf'
        m_pdf.assert_called_once()

    def test_gerar_xls_success(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa geração de relatório XLS com sucesso.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        with patch.object(resultado_escolha_service, 'render_to_xls', return_value=HttpResponse(b'xlsx', content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')) as m_xls:
            response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='xls', cabecalho='Cabeçalho Teste')
        assert isinstance(response, HttpResponse)
        m_xls.assert_called_once()

    def test_gerar_docx_success(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa geração de relatório DOCX com sucesso.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        with patch.object(resultado_escolha_service, 'render_to_docx', return_value=HttpResponse(b'docx', content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')) as m_docx:
            response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='docx', cabecalho='Cabeçalho Teste')
        assert isinstance(response, HttpResponse)
        m_docx.assert_called_once()

    def test_gerar_com_cabecalho_padrao(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa que usa cabeçalho padrão automaticamente quando preenchido.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.context['cabecalho_padrao'] = 'Cabeçalho Padrão'
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [mock_escolhas_response, [], []]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')) as m_render:
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html', cabecalho='')
        _, args, kwargs = m_render.mock_calls[0]
        context = args[2] if len(args) >= 3 else kwargs.get('context')
        assert context['cabecalho_padrao'] == 'Cabeçalho Padrão'

    def test_gerar_tipo_resultado_escolha_unificado(self, settings: Any, configuracao_relatorio: Any, parametrizacao: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa geração com tipo RESULTADO_ESCOLHA unificado (busca todas as.
        
        Args:
            self: Instância do objeto.
            settings: Parâmetro settings da operação.
            configuracao_relatorio: Parâmetro configuracao relatorio da operação.
            parametrizacao: Parâmetro parametrizacao da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        settings.ESCOLHAS_API_URL = 'http://escolhas'
        settings.CANDIDATOS_API_URL = 'http://candidatos'
        settings.PROCESSOS_API_URL = 'http://processos'
        settings.AGENDAS_API_URL = 'http://agendas'
        settings.RELATORIO_CABECALHO_PADRAO = 'Padrão'
        service = ResultadoEscolha(tipo='RESULTADO_ESCOLHA', configuracao=configuracao_relatorio, parametrizacao=parametrizacao)
        service.processos_service = Mock()
        service.agendas_service = Mock()
        service.candidatos_service = Mock()
        service.escolhas_service = Mock()
        service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        escolhas_com_situacao = [{**item, 'situacao': 'escolha'} if isinstance(item, dict) else item for item in mock_escolhas_response]
        service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [escolhas_com_situacao, [], []]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        assert service.escolhas_service.buscar_escolhas_por_candidatos.call_count == 3
        assert len(dados) > 0
        assert 'tipos_escolha' in dados[0]
        tipos_encontrados = [t.get('nome') for t in dados[0].get('tipos_escolha', [])]
        assert 'Escolha' in tipos_encontrados

    def test_gerar_tipo_resultado_escolha_com_nao_escolha(self, settings: Any, configuracao_relatorio: Any, parametrizacao: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa geração com tipo RESULTADO_ESCOLHA incluindo não escolha.
        
        Args:
            self: Instância do objeto.
            settings: Parâmetro settings da operação.
            configuracao_relatorio: Parâmetro configuracao relatorio da operação.
            parametrizacao: Parâmetro parametrizacao da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        settings.ESCOLHAS_API_URL = 'http://escolhas'
        settings.CANDIDATOS_API_URL = 'http://candidatos'
        settings.PROCESSOS_API_URL = 'http://processos'
        settings.AGENDAS_API_URL = 'http://agendas'
        settings.RELATORIO_CABECALHO_PADRAO = 'Padrão'
        service = ResultadoEscolha(tipo='RESULTADO_ESCOLHA', configuracao=configuracao_relatorio, parametrizacao=parametrizacao)
        service.processos_service = Mock()
        service.agendas_service = Mock()
        service.candidatos_service = Mock()
        service.escolhas_service = Mock()
        service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [[], mock_escolhas_response, []]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        assert service.escolhas_service.buscar_escolhas_por_candidatos.call_count == 3

    def test_gerar_escolha_valor_r_reconvocacao(self, settings: Any, configuracao_relatorio: Any, parametrizacao: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_candidatos_response: Any) -> None:
        """Testa que escolha valor é 'R' para reconvocação no tipo unificado.
        
        Args:
            self: Instância do objeto.
            settings: Parâmetro settings da operação.
            configuracao_relatorio: Parâmetro configuracao relatorio da operação.
            parametrizacao: Parâmetro parametrizacao da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        settings.ESCOLHAS_API_URL = 'http://escolhas'
        settings.CANDIDATOS_API_URL = 'http://candidatos'
        settings.PROCESSOS_API_URL = 'http://processos'
        settings.AGENDAS_API_URL = 'http://agendas'
        settings.RELATORIO_CABECALHO_PADRAO = 'Padrão'
        service = ResultadoEscolha(tipo='RESULTADO_ESCOLHA', configuracao=configuracao_relatorio, parametrizacao=parametrizacao)
        service.processos_service = Mock()
        service.agendas_service = Mock()
        service.candidatos_service = Mock()
        service.escolhas_service = Mock()
        service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [[], [], [{'candidato_uuid': 'candidato-uuid-1', 'situacao': 'reconvocacao'}]]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        cargos = dados
        for cargo in cargos:
            if 'tipos_escolha' in cargo:
                for tipo_escolha in cargo.get('tipos_escolha', []):
                    if tipo_escolha.get('nome') == 'Reconvocação':
                        for agenda in tipo_escolha.get('agendas', []):
                            for candidato in agenda.get('candidatos', []):
                                assert candidato.get('escolha') == 'R'

    def test_gerar_escolha_valor_n_nao_escolha(self, settings: Any, configuracao_relatorio: Any, parametrizacao: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_candidatos_response: Any) -> None:
        """Testa que escolha valor é 'N' para não escolha no tipo unificado.
        
        Args:
            self: Instância do objeto.
            settings: Parâmetro settings da operação.
            configuracao_relatorio: Parâmetro configuracao relatorio da operação.
            parametrizacao: Parâmetro parametrizacao da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        settings.ESCOLHAS_API_URL = 'http://escolhas'
        settings.CANDIDATOS_API_URL = 'http://candidatos'
        settings.PROCESSOS_API_URL = 'http://processos'
        settings.AGENDAS_API_URL = 'http://agendas'
        settings.RELATORIO_CABECALHO_PADRAO = 'Padrão'
        service = ResultadoEscolha(tipo='RESULTADO_ESCOLHA', configuracao=configuracao_relatorio, parametrizacao=parametrizacao)
        service.processos_service = Mock()
        service.agendas_service = Mock()
        service.candidatos_service = Mock()
        service.escolhas_service = Mock()
        service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [[], [{'candidato_uuid': 'candidato-uuid-1', 'situacao': 'nao-escolha'}], []]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        for cargo in dados:
            if 'tipos_escolha' in cargo:
                for tipo_escolha in cargo.get('tipos_escolha', []):
                    if tipo_escolha.get('nome') == 'Não Escolha':
                        for agenda in tipo_escolha.get('agendas', []):
                            for candidato in agenda.get('candidatos', []):
                                assert candidato.get('escolha') == 'N'

    def test_gerar_escolha_valor_s(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_candidatos_response: Any) -> None:
        """Testa que escolha valor é 'S' para escolha sim no tipo unificado.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [[{'candidato_uuid': 'candidato-uuid-1', 'situacao': 'escolha'}], [], []]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        for cargo in dados:
            if 'tipos_escolha' in cargo:
                for tipo_escolha in cargo.get('tipos_escolha', []):
                    if tipo_escolha.get('nome') == 'Escolha':
                        for agenda in tipo_escolha.get('agendas', []):
                            for candidato in agenda.get('candidatos', []):
                                assert candidato.get('escolha') == 'S'

    def test_gerar_erro_buscar_candidatos(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_agendas_response: Any) -> None:
        """Testa que erro ao buscar candidatos é propagado.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.side_effect = Exception('Erro API')
        with pytest.raises(Exception, match='Erro API'):
            resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')

    def test_gerar_erro_buscar_escolhas(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_candidatos_response: Any) -> None:
        """Testa que erro ao buscar escolhas é tratado e continua (para.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [Exception('Erro Escolhas'), [], []]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        assert isinstance(response, HttpResponse)

    def test_gerar_sem_candidato_na_escolha(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_candidatos_response: Any) -> None:
        """Testa que escolhas sem candidato_uuid são ignoradas.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [[{'candidato_uuid': None}, {'candidato_uuid': 'candidato-uuid-1'}], [], []]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        total_candidatos = 0
        for cargo in dados:
            if 'tipos_escolha' in cargo:
                for tipo_escolha in cargo.get('tipos_escolha', []):
                    for agenda in tipo_escolha.get('agendas', []):
                        total_candidatos += len(agenda.get('candidatos', []))
            else:
                for agenda in cargo.get('agendas', []):
                    total_candidatos += len(agenda.get('candidatos', []))
        assert total_candidatos == 1

    def test_gerar_candidato_nao_encontrado(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_candidatos_response: Any) -> None:
        """Testa que escolhas com candidato não encontrado são ignoradas.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [[{'candidato_uuid': 'candidato-inexistente'}], [], []]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        total_candidatos = 0
        for cargo in dados:
            if 'tipos_escolha' in cargo:
                for tipo_escolha in cargo.get('tipos_escolha', []):
                    for agenda in tipo_escolha.get('agendas', []):
                        total_candidatos += len(agenda.get('candidatos', []))
            else:
                for agenda in cargo.get('agendas', []):
                    total_candidatos += len(agenda.get('candidatos', []))
        assert total_candidatos == 0

    def test_gerar_agenda_nao_encontrada_cria_vazia(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_candidatos_response: Any) -> None:
        """Testa que quando agenda não é encontrada, cria uma vazia.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = _MockResponse({'results': []})
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [[{'candidato_uuid': 'candidato-uuid-1'}], [], []]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        assert len(dados) > 0
        if 'tipos_escolha' in dados[0]:
            assert len(dados[0]['tipos_escolha']) > 0
            assert len(dados[0]['tipos_escolha'][0]['agendas']) > 0
            assert dados[0]['tipos_escolha'][0]['agendas'][0]['uuid'] is None
        else:
            assert dados[0]['agendas'][0]['uuid'] is None

    def test_gerar_erro_buscar_cargos_continua(self, resultado_escolha_service: Any, mock_agendas_response: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa que erro ao buscar cargos não interrompe o processo.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.side_effect = Exception('Erro Cargos')
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [mock_escolhas_response, [], []]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        assert isinstance(response, HttpResponse)

    def test_gerar_erro_buscar_agendas_continua(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa que erro ao buscar agendas não interrompe o processo.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.side_effect = Exception('Erro Agendas')
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [mock_escolhas_response, [], []]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        assert isinstance(response, HttpResponse)

    def test_gerar_candidatos_lista_direta(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_escolhas_response: Any) -> None:
        """Testa quando candidatos vem como lista direta (não dict com results).
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        candidatos_lista = [{'uuid': 'candidato-uuid-1', 'codigo_cargo': '123', 'classificacao': 1, 'candidato': {'nome': 'João', 'rg': '123', 'cpf': '123'}}]
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = _MockResponse(candidatos_lista)
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [mock_escolhas_response, [], []]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        assert isinstance(response, HttpResponse)

    def test_gerar_cargo_descricao_fallback(self, resultado_escolha_service: Any, mock_agendas_response: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa fallback de descrição de cargo quando não encontrada.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        cargos_response = _MockResponse([{'cargo_codigo': '123', 'cargo_nome': ''}])
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = _MockResponse({'results': []})
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [mock_escolhas_response, [], []]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        assert isinstance(response, HttpResponse)

    def test_gerar_cargo_codigo_int(self, resultado_escolha_service: Any, mock_agendas_response: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa quando código do cargo é inteiro.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        cargos_response = _MockResponse([{'cargo_codigo': 123, 'cargo_nome': 'Professor'}])
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [mock_escolhas_response, [], []]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        assert isinstance(response, HttpResponse)

    def test_gerar_candidato_sem_candidato_obj(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_escolhas_response: Any) -> None:
        """Testa quando candidato não tem objeto candidato.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        candidatos_response = _MockResponse({'results': [{'uuid': 'candidato-uuid-1', 'codigo_cargo': '123', 'classificacao': 1, 'candidato': None}]})
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [mock_escolhas_response, [], []]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        assert isinstance(response, HttpResponse)

    def test_gerar_agenda_encontrada_por_cargo(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa quando agenda é encontrada pelo cargo do candidato.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        agenda_response = _MockResponse({'results': [{'uuid': 'agenda-uuid-1', 'cargo_codigo': '123', 'cargo_nome': 'Professor', 'candidatos_uuids': [], 'escolha_em': '2026-01-05', 'sessao': '1'}]})
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = agenda_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [mock_escolhas_response, [], []]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        assert isinstance(response, HttpResponse)

    def test_gerar_formato_csv(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa geração com formato CSV (tratado como XLS).
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [mock_escolhas_response, [], []]
        with patch.object(resultado_escolha_service, 'render_to_xls', return_value=HttpResponse(b'xlsx', content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')) as m_xls:
            response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='csv')
        assert isinstance(response, HttpResponse)
        m_xls.assert_called_once()

    def test_gerar_formato_doc(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa geração com formato DOC (tratado como DOCX).
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [mock_escolhas_response, [], []]
        with patch.object(resultado_escolha_service, 'render_to_docx', return_value=HttpResponse(b'docx', content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')) as m_docx:
            response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='doc')
        assert isinstance(response, HttpResponse)
        m_docx.assert_called_once()

    def test_gerar_tipo_invalido(self, settings: Any, configuracao_relatorio: Any, parametrizacao: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa geração com tipo inválido (não RESULTADO_ESCOLHA).
        
        Args:
            self: Instância do objeto.
            settings: Parâmetro settings da operação.
            configuracao_relatorio: Parâmetro configuracao relatorio da operação.
            parametrizacao: Parâmetro parametrizacao da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        settings.ESCOLHAS_API_URL = 'http://escolhas'
        settings.CANDIDATOS_API_URL = 'http://candidatos'
        settings.PROCESSOS_API_URL = 'http://processos'
        settings.AGENDAS_API_URL = 'http://agendas'
        settings.RELATORIO_CABECALHO_PADRAO = 'Padrão'
        config_invalida = ConfiguracaoRelatorio.objects.create(tipo='TIPO_INVALIDO', usar_logotipo=False, cabecalho='', texto_final='', cabecalho_capa_ata='')
        service = ResultadoEscolha(tipo='TIPO_INVALIDO', configuracao=config_invalida, parametrizacao=parametrizacao)
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
                response, dados = service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        for cargo in dados:
            for agenda in cargo.get('agendas', []):
                for candidato in agenda.get('candidatos', []):
                    assert candidato.get('escolha') == '-'

    def test_gerar_cargo_sem_descricao_sem_codigo(self, resultado_escolha_service: Any, mock_agendas_response: Any, mock_escolhas_response: Any) -> None:
        """Testa quando candidato não tem descrição nem código de cargo.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        candidatos_response = _MockResponse({'results': [{'uuid': 'candidato-uuid-1', 'codigo_cargo': '', 'descricao_cargo': '', 'classificacao': 1, 'candidato': {'nome': 'João', 'rg': '123', 'cpf': '123'}}]})
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = _MockResponse([])
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = _MockResponse({'results': []})
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        assert len(dados) > 0
        assert dados[0]['descricao'] == 'Cargo não informado'

    def test_gerar_agenda_sem_descricao_busca_mapa(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa quando agenda não tem descrição e busca no mapa de cargos.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        agenda_response = _MockResponse({'results': [{'uuid': 'agenda-uuid-1', 'cargo_codigo': '123', 'cargo_nome': '', 'candidatos_uuids': ['candidato-uuid-1'], 'escolha_em': '2026-01-05', 'sessao': '1'}]})
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = agenda_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        assert isinstance(response, HttpResponse)

    def test_gerar_agenda_sem_descricao_sem_mapa(self, resultado_escolha_service: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa quando agenda não tem descrição e não encontra no mapa.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        agenda_response = _MockResponse({'results': [{'uuid': 'agenda-uuid-1', 'cargo_codigo': '999', 'cargo_nome': '', 'candidatos_uuids': ['candidato-uuid-1'], 'escolha_em': '2026-01-05', 'sessao': '1'}]})
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = _MockResponse([])
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = agenda_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        assert isinstance(response, HttpResponse)
        assert len(dados) > 0
        assert 'Cargo 999' in dados[0]['descricao'] or dados[0]['descricao'] == 'Cargo 999'

    def test_gerar_agenda_sem_descricao_sem_codigo(self, resultado_escolha_service: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa quando agenda não tem descrição nem código.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        agenda_response = _MockResponse({'results': [{'uuid': 'agenda-uuid-1', 'cargo_codigo': '', 'cargo_nome': '', 'candidatos_uuids': ['candidato-uuid-1'], 'escolha_em': '2026-01-05', 'sessao': '1'}]})
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = _MockResponse([])
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = agenda_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        assert isinstance(response, HttpResponse)
        assert len(dados) > 0
        assert dados[0]['descricao'] == 'Cargo não informado'

    def test_render_to_xls_exception(self, resultado_escolha_service: Any) -> None:
        """Testa tratamento de exceção no render_to_xls.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        cargos_list = [{'descricao': 'Professor', 'agendas': []}]
        with patch('relatorios.services.relatorios.resultado_escolha.Workbook', side_effect=Exception('Erro Excel')):
            with pytest.raises(Exception, match='Erro Excel'):
                resultado_escolha_service.render_to_xls(cargos_list, 'Cabeçalho', '', filename='test.xlsx')

class TestRenderToXls:
    """Testes para o método render_to_xls."""

    def test_render_to_xls_success(self, resultado_escolha_service: Any) -> None:
        """Testa geração de Excel com sucesso.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        cargos_list = [{'descricao': 'Professor', 'agendas': [{'sessao': '1', 'candidatos': [{'classificacao_geral': 1, 'classificacao_nna': 5, 'classificacao_def': '-', 'nome': 'João', 'rg': '123', 'cpf': '123', 'escolha': 'S'}]}]}]
        response = resultado_escolha_service.render_to_xls(cargos_list, 'Cabeçalho Teste', '', filename='test.xlsx')
        assert isinstance(response, HttpResponse)
        assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response['Content-Type']
        assert 'attachment' in response['Content-Disposition']
        assert 'test.xlsx' in response['Content-Disposition']

    def test_render_to_xls_sem_cabecalho(self, resultado_escolha_service: Any) -> None:
        """Testa geração de Excel sem cabeçalho.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        cargos_list = [{'descricao': 'Professor', 'agendas': []}]
        response = resultado_escolha_service.render_to_xls(cargos_list, '', '', filename='test.xlsx')
        assert isinstance(response, HttpResponse)

    def test_render_to_xls_multiplos_cargos(self, resultado_escolha_service: Any) -> None:
        """Testa geração de Excel com múltiplos cargos.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        cargos_list = [{'descricao': 'Professor A', 'agendas': [{'sessao': '1', 'candidatos': [{'classificacao_geral': 1, 'nome': 'João', 'rg': '1', 'cpf': '1', 'escolha': 'S', 'classificacao_nna': '-', 'classificacao_def': '-'}]}]}, {'descricao': 'Professor B', 'agendas': [{'sessao': '2', 'candidatos': [{'classificacao_geral': 2, 'nome': 'Maria', 'rg': '2', 'cpf': '2', 'escolha': 'S', 'classificacao_nna': '-', 'classificacao_def': '-'}]}]}]
        response = resultado_escolha_service.render_to_xls(cargos_list, 'Cabeçalho', '', filename='test.xlsx')
        assert isinstance(response, HttpResponse)

    @patch('relatorios.services.relatorios.resultado_escolha.OPENPYXL_AVAILABLE', False)
    def test_render_to_xls_openpyxl_nao_disponivel(self, resultado_escolha_service: Any) -> None:
        """Testa erro quando openpyxl não está disponível.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        cargos_list = []  # type: ignore[var-annotated]
        with pytest.raises(ImportError, match='openpyxl'):
            resultado_escolha_service.render_to_xls(cargos_list, 'Cabeçalho', '', filename='test.xlsx')

class TestRenderToDocx:
    """Testes para o método render_to_docx."""

    @patch('relatorios.services.relatorios.resultado_escolha.DOCX_AVAILABLE', False)
    def test_render_to_docx_python_docx_nao_disponivel(self, resultado_escolha_service: Any) -> None:
        """Testa erro quando python-docx não está disponível.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        cargos_list = []  # type: ignore[var-annotated]
        with pytest.raises(ImportError, match='python-docx'):
            resultado_escolha_service.render_to_docx(cargos_list, 'Cabeçalho', 'test.docx')

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
    def test_render_to_docx_completo_com_cabecalho(self, mock_bytesio: Any, mock_timezone: Any, mock_oxml_element: Any, mock_qn: Any, mock_wd_align: Any, mock_rgb_color: Any, mock_pt: Any, mock_inches: Any, mock_document: Any, resultado_escolha_service: Any) -> None:
        """Testa geração completa de Word com cabeçalho e dados.
        
        Args:
            self: Instância do objeto.
            mock_bytesio: Parâmetro mock bytesio da operação.
            mock_timezone: Parâmetro mock timezone da operação.
            mock_oxml_element: Parâmetro mock oxml element da operação.
            mock_qn: Parâmetro mock qn da operação.
            mock_wd_align: Parâmetro mock wd align da operação.
            mock_rgb_color: Parâmetro mock rgb color da operação.
            mock_pt: Parâmetro mock pt da operação.
            mock_inches: Parâmetro mock inches da operação.
            mock_document: Parâmetro mock document da operação.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
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
        for _i in range(8):
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
        for _i in range(8):
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
        mock_qn.return_value = 'w:shd'
        mock_oxml_element.return_value = MagicMock()
        cargos_list = [{'descricao': 'Professor de Educação Infantil', 'agendas': [{'sessao': '1', 'candidatos': [{'classificacao_geral': 1, 'classificacao_nna': 5, 'classificacao_def': '-', 'nome': 'João Silva', 'rg': '123456789', 'cpf': '12345678901', 'escolha': 'S'}]}]}]
        response = resultado_escolha_service.render_to_docx(cargos_list, '<b>Cabeçalho Teste</b>', 'test.docx')
        assert isinstance(response, HttpResponse)
        assert 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in response['Content-Type']
        assert 'attachment' in response['Content-Disposition']
        assert 'test.docx' in response['Content-Disposition'] or 'resultado_escolha.docx' in response['Content-Disposition']
        mock_document.assert_called_once()
        assert mock_section.top_margin is not None
        assert mock_section.bottom_margin is not None
        assert mock_section.left_margin is not None
        assert mock_section.right_margin is not None
        assert mock_doc.add_paragraph.call_count >= 4
        mock_doc.add_table.assert_called_once()
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
    def test_render_to_docx_sem_cabecalho(self, mock_bytesio: Any, mock_timezone: Any, mock_oxml_element: Any, mock_qn: Any, mock_wd_align: Any, mock_rgb_color: Any, mock_pt: Any, mock_inches: Any, mock_document: Any, resultado_escolha_service: Any) -> None:
        """Testa geração de Word sem cabeçalho.
        
        Args:
            self: Instância do objeto.
            mock_bytesio: Parâmetro mock bytesio da operação.
            mock_timezone: Parâmetro mock timezone da operação.
            mock_oxml_element: Parâmetro mock oxml element da operação.
            mock_qn: Parâmetro mock qn da operação.
            mock_wd_align: Parâmetro mock wd align da operação.
            mock_rgb_color: Parâmetro mock rgb color da operação.
            mock_pt: Parâmetro mock pt da operação.
            mock_inches: Parâmetro mock inches da operação.
            mock_document: Parâmetro mock document da operação.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
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
        for _i in range(8):
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
        mock_inches.return_value = MagicMock()
        mock_pt.return_value = MagicMock()
        mock_rgb_color.return_value = MagicMock()
        mock_wd_align.CENTER = 'CENTER'
        mock_wd_align.LEFT = 'LEFT'
        mock_qn.return_value = 'w:shd'
        mock_oxml_element.return_value = MagicMock()
        cargos_list = [{'descricao': 'Professor', 'agendas': []}]
        response = resultado_escolha_service.render_to_docx(cargos_list, '', 'test.docx')
        assert isinstance(response, HttpResponse)
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
    def test_render_to_docx_multiplos_cargos_e_candidatos(self, mock_bytesio: Any, mock_timezone: Any, mock_oxml_element: Any, mock_qn: Any, mock_wd_align: Any, mock_rgb_color: Any, mock_pt: Any, mock_inches: Any, mock_document: Any, resultado_escolha_service: Any) -> Any:
        """Testa geração de Word com múltiplos cargos e candidatos.
        
        Args:
            self: Instância do objeto.
            mock_bytesio: Parâmetro mock bytesio da operação.
            mock_timezone: Parâmetro mock timezone da operação.
            mock_oxml_element: Parâmetro mock oxml element da operação.
            mock_qn: Parâmetro mock qn da operação.
            mock_wd_align: Parâmetro mock wd align da operação.
            mock_rgb_color: Parâmetro mock rgb color da operação.
            mock_pt: Parâmetro mock pt da operação.
            mock_inches: Parâmetro mock inches da operação.
            mock_document: Parâmetro mock document da operação.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Nenhum valor; valida comportamento via asserções.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
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
        for _i in range(8):
            mock_cell = MagicMock()
            mock_cell.paragraphs = [MagicMock()]
            mock_cell.paragraphs[0].runs = [MagicMock()]
            mock_cell._element = MagicMock()
            mock_cell._element.get_or_add_tcPr.return_value = MagicMock()
            mock_cell._element.get_or_add_tcPr.return_value.find.return_value = None
            mock_header_cells.append(mock_cell)
        mock_header_row.cells = mock_header_cells
        mock_table.rows = [mock_header_row]

        def create_data_row() -> Any:
            """Executa create data row.
            
            Returns:
                Resultado da operação.
            
            Raises:
                Nenhuma exceção específica documentada.
            """
            mock_row = MagicMock()
            mock_cells = []
            for _i in range(8):
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
        cargos_list = [{'descricao': 'Professor A', 'agendas': [{'sessao': '1', 'candidatos': [{'classificacao_geral': 1, 'classificacao_nna': '-', 'classificacao_def': '-', 'nome': 'João', 'rg': '1', 'cpf': '1', 'escolha': 'S'}, {'classificacao_geral': 2, 'classificacao_nna': '-', 'classificacao_def': '-', 'nome': 'Maria', 'rg': '2', 'cpf': '2', 'escolha': 'S'}]}]}, {'descricao': 'Professor B', 'agendas': [{'sessao': '2', 'candidatos': [{'classificacao_geral': 1, 'classificacao_nna': '-', 'classificacao_def': '-', 'nome': 'Pedro', 'rg': '3', 'cpf': '3', 'escolha': 'N'}]}]}]
        response = resultado_escolha_service.render_to_docx(cargos_list, 'Cabeçalho', 'test.docx')
        assert isinstance(response, HttpResponse)
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
    def test_render_to_docx_com_existing_shd(self, mock_bytesio: Any, mock_timezone: Any, mock_oxml_element: Any, mock_qn: Any, mock_wd_align: Any, mock_rgb_color: Any, mock_pt: Any, mock_inches: Any, mock_document: Any, resultado_escolha_service: Any) -> None:
        """Testa quando já existe shading element (existing_shd).
        
        Args:
            self: Instância do objeto.
            mock_bytesio: Parâmetro mock bytesio da operação.
            mock_timezone: Parâmetro mock timezone da operação.
            mock_oxml_element: Parâmetro mock oxml element da operação.
            mock_qn: Parâmetro mock qn da operação.
            mock_wd_align: Parâmetro mock wd align da operação.
            mock_rgb_color: Parâmetro mock rgb color da operação.
            mock_pt: Parâmetro mock pt da operação.
            mock_inches: Parâmetro mock inches da operação.
            mock_document: Parâmetro mock document da operação.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        mock_doc = MagicMock()
        mock_document.return_value = mock_doc
        mock_section = MagicMock()
        mock_doc.sections = [mock_section]
        mock_paragraph = MagicMock()
        mock_run = MagicMock()
        mock_paragraph.add_run.return_value = mock_run
        mock_paragraph._element = MagicMock()
        mock_p_pr = MagicMock()
        mock_existing_shd = MagicMock()
        mock_p_pr.find.return_value = mock_existing_shd
        mock_paragraph._element.get_or_add_pPr.return_value = mock_p_pr
        mock_doc.add_paragraph.return_value = mock_paragraph
        mock_table = MagicMock()
        mock_header_row = MagicMock()
        mock_header_cells = []
        for _i in range(8):
            mock_cell = MagicMock()
            mock_cell.paragraphs = [MagicMock()]
            mock_cell.paragraphs[0].runs = [MagicMock()]
            mock_cell._element = MagicMock()
            mock_tc_pr = MagicMock()
            mock_existing_shd_cell = MagicMock()
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
        mock_inches.return_value = MagicMock()
        mock_pt.return_value = MagicMock()
        mock_rgb_color.return_value = MagicMock()
        mock_wd_align.CENTER = 'CENTER'
        mock_wd_align.LEFT = 'LEFT'
        mock_qn.return_value = 'w:shd'
        mock_oxml_element.return_value = MagicMock()
        cargos_list = [{'descricao': 'Professor', 'agendas': [{'sessao': '1', 'candidatos': [{'classificacao_geral': 1, 'classificacao_nna': '-', 'classificacao_def': '-', 'nome': 'João', 'rg': '1', 'cpf': '1', 'escolha': 'S'}]}]}]
        response = resultado_escolha_service.render_to_docx(cargos_list, 'Cabeçalho', 'test.docx')
        assert isinstance(response, HttpResponse)
        assert mock_p_pr.remove.called

    @patch('relatorios.services.relatorios.resultado_escolha.DOCX_AVAILABLE', True)
    @patch('relatorios.services.relatorios.resultado_escolha.Document')
    def test_render_to_docx_exception(self, mock_document: Any, resultado_escolha_service: Any) -> None:
        """Testa tratamento de exceção no render_to_docx.
        
        Args:
            self: Instância do objeto.
            mock_document: Parâmetro mock document da operação.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        mock_document.side_effect = Exception('Erro ao criar documento')
        cargos_list = [{'descricao': 'Professor', 'agendas': []}]
        with pytest.raises(Exception, match='Erro ao criar documento'):
            resultado_escolha_service.render_to_docx(cargos_list, 'Cabeçalho', 'test.docx')

    def test_agrupar_por_cargo_sem_agenda_uuid(self, resultado_escolha_service: Any) -> None:
        """Testa agrupamento quando agenda não tem UUID.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        escolhas = [{'cargo_codigo': '123', 'cargo_descricao': 'Professor', 'agenda_uuid': None, 'agenda_nome': 'Agenda 1', 'agenda_data': '2026-01-05', 'agenda_sessao': '1', 'classificacao_geral': 1, 'nome': 'João'}]
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        assert len(resultado) == 1
        assert resultado[0]['codigo'] == '123'
        assert len(resultado[0]['agendas']) == 1
        assert resultado[0]['agendas'][0]['uuid'] is None

    def test_agrupar_por_cargo_sessao_nao_numerica(self, resultado_escolha_service: Any) -> None:
        """Testa agrupamento quando sessão não é numérica.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        escolhas = [{'cargo_codigo': '123', 'cargo_descricao': 'Professor', 'agenda_uuid': 'agenda-1', 'agenda_nome': 'Agenda 1', 'agenda_data': '2026-01-05', 'agenda_sessao': 'Especial', 'classificacao_geral': 1, 'nome': 'João'}]
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        assert len(resultado) == 1
        assert resultado[0]['agendas'][0]['sessao'] == 'Especial'

    def test_agrupar_por_cargo_classificacao_infinito(self, resultado_escolha_service: Any) -> None:
        """Testa ordenação quando classificação não é numérica.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        escolhas = [{'cargo_codigo': '123', 'cargo_descricao': 'Professor', 'agenda_uuid': 'agenda-1', 'agenda_nome': 'Agenda 1', 'agenda_data': '2026-01-05', 'agenda_sessao': '1', 'classificacao_geral': '-', 'nome': 'João'}, {'cargo_codigo': '123', 'cargo_descricao': 'Professor', 'agenda_uuid': 'agenda-1', 'agenda_nome': 'Agenda 1', 'agenda_data': '2026-01-05', 'agenda_sessao': '1', 'classificacao_geral': 1, 'nome': 'Maria'}]
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        candidatos = resultado[0]['agendas'][0]['candidatos']
        assert candidatos[0]['classificacao_geral'] == 1
        assert candidatos[1]['classificacao_geral'] == '-'

    def test_agrupar_por_cargo_ordenacao_agendas(self, resultado_escolha_service: Any) -> None:
        """Testa ordenação de agendas por data e sessão.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        escolhas = [{'cargo_codigo': '123', 'cargo_descricao': 'Professor', 'agenda_uuid': 'agenda-2', 'agenda_nome': 'Agenda 2', 'agenda_data': '2026-01-06', 'agenda_sessao': '1', 'classificacao_geral': 1, 'nome': 'João'}, {'cargo_codigo': '123', 'cargo_descricao': 'Professor', 'agenda_uuid': 'agenda-1', 'agenda_nome': 'Agenda 1', 'agenda_data': '2026-01-05', 'agenda_sessao': '1', 'classificacao_geral': 1, 'nome': 'Maria'}]
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        agendas = resultado[0]['agendas']
        assert agendas[0]['data'] == '2026-01-05'
        assert agendas[1]['data'] == '2026-01-06'

    def test_agrupar_por_cargo_ordenacao_cargos(self, resultado_escolha_service: Any) -> None:
        """Testa ordenação de cargos por descrição.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        escolhas = [{'cargo_codigo': '456', 'cargo_descricao': 'Professor B', 'agenda_uuid': 'agenda-1', 'agenda_nome': 'Agenda 1', 'agenda_data': '2026-01-05', 'agenda_sessao': '1', 'classificacao_geral': 1, 'nome': 'João'}, {'cargo_codigo': '123', 'cargo_descricao': 'Professor A', 'agenda_uuid': 'agenda-2', 'agenda_nome': 'Agenda 2', 'agenda_data': '2026-01-05', 'agenda_sessao': '1', 'classificacao_geral': 1, 'nome': 'Maria'}]
        resultado = resultado_escolha_service._agrupar_por_cargo_e_agenda(escolhas)
        assert resultado[0]['descricao'] == 'Professor A'
        assert resultado[1]['descricao'] == 'Professor B'

class TestAgruparPorCargoTipoEscolhaEAgenda:
    """Testes para o método _agrupar_por_cargo_tipo_escolha_e_agenda."""

    def test_agrupar_por_cargo_tipo_escolha_e_agenda_basico(self, resultado_escolha_service: Any) -> None:
        """Testa agrupamento básico por cargo, tipo de escolha e agenda.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        escolhas = [{'cargo_codigo': '123', 'cargo_descricao': 'Professor', 'tipo_escolha': 'Escolha', 'tipo_escolha_ordem': 1, 'agenda_uuid': 'agenda-1', 'agenda_nome': 'Agenda 1', 'agenda_data': '2026-01-05', 'agenda_sessao': '1', 'classificacao_geral': 1, 'classificacao_def': '-', 'classificacao_nna': '-', 'nome': 'João', 'rg': '123', 'cpf': '123', 'escolha': 'S'}, {'cargo_codigo': '123', 'cargo_descricao': 'Professor', 'tipo_escolha': 'Não Escolha', 'tipo_escolha_ordem': 2, 'agenda_uuid': 'agenda-1', 'agenda_nome': 'Agenda 1', 'agenda_data': '2026-01-05', 'agenda_sessao': '1', 'classificacao_geral': 2, 'classificacao_def': '-', 'classificacao_nna': '-', 'nome': 'Maria', 'rg': '456', 'cpf': '456', 'escolha': 'N'}]
        resultado = resultado_escolha_service._agrupar_por_cargo_tipo_escolha_e_agenda(escolhas)
        assert len(resultado) == 1
        assert resultado[0]['codigo'] == '123'
        assert len(resultado[0]['tipos_escolha']) == 2
        assert resultado[0]['tipos_escolha'][0]['nome'] == 'Escolha'
        assert resultado[0]['tipos_escolha'][1]['nome'] == 'Não Escolha'

class TestAdicionarResumoDreEscola:
    """Testes para o método _adicionar_resumo_dre_escola."""

    def test_adicionar_resumo_dre_escola_basico(self, resultado_escolha_service: Any) -> None:
        """Testa adição básica de resumo DRE/Escola.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        cargos_list = [{'codigo': '123', 'descricao': 'Professor', 'tipos_escolha': []}]
        escolhas_realizadas = [{'cargo_codigo': '123', 'tipo_escolha': 'Escolha', 'dre_codigo': 'DRE001', 'dre_nome': 'DRE Butantã', 'escola_codigo_eol': '12345', 'escola_nome': 'EMEF Teste', 'tipo_ue': 'EMEF', 'tipo_vaga': 'definitiva'}, {'cargo_codigo': '123', 'tipo_escolha': 'Escolha', 'dre_codigo': 'DRE001', 'dre_nome': 'DRE Butantã', 'escola_codigo_eol': '12345', 'escola_nome': 'EMEF Teste', 'tipo_ue': 'EMEF', 'tipo_vaga': 'precaria'}]
        mock_vagas_response = Mock()
        mock_vagas_response.json.return_value = {'vagas': [{'cargo_codigo': '123', 'escola': {'codigo_eol': '12345', 'dre': {'codigo': 'DRE001'}}, 'vagas_definitivas': 5, 'vagas_precarias': 3}]}
        resultado_escolha_service.escolhas_service.buscar_vagas_escolas = Mock(return_value=mock_vagas_response)
        resultado = resultado_escolha_service._adicionar_resumo_dre_escola(cargos_list, escolhas_realizadas, 'proc-123')
        assert len(resultado) == 1
        assert 'resumo_dre_escola' in resultado[0]
        assert len(resultado[0]['resumo_dre_escola']) == 1
        assert resultado[0]['resumo_dre_escola'][0]['nome'] == 'DRE Butantã'
        assert len(resultado[0]['resumo_dre_escola'][0]['escolas']) == 1
        escola = resultado[0]['resumo_dre_escola'][0]['escolas'][0]
        assert escola['nome'] == 'EMEF Teste'
        assert escola['qtd_escolhas_definitivas'] == 1
        assert escola['qtd_escolhas_precarias'] == 1
        assert escola['qtd_vagas_definitivas'] == 5
        assert escola['qtd_vagas_precarias'] == 3

    def test_adicionar_resumo_dre_escola_sem_vagas(self, resultado_escolha_service: Any) -> None:
        """Testa resumo DRE/Escola quando não há vagas retornadas.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        cargos_list = [{'codigo': '123', 'descricao': 'Professor', 'tipos_escolha': []}]
        escolhas_realizadas = [{'cargo_codigo': '123', 'tipo_escolha': 'Escolha', 'dre_codigo': 'DRE001', 'dre_nome': 'DRE Butantã', 'escola_codigo_eol': '12345', 'escola_nome': 'EMEF Teste', 'tipo_ue': 'EMEF', 'tipo_vaga': 'definitiva'}]
        resultado_escolha_service.escolhas_service.buscar_vagas_escolas = Mock(side_effect=Exception('Erro'))
        resultado = resultado_escolha_service._adicionar_resumo_dre_escola(cargos_list, escolhas_realizadas, 'proc-123')
        assert len(resultado) == 1
        assert 'resumo_dre_escola' in resultado[0]
        escola = resultado[0]['resumo_dre_escola'][0]['escolas'][0]
        assert escola['qtd_vagas_definitivas'] == 0
        assert escola['qtd_vagas_precarias'] == 0

class TestRenderToXlsResumoDreEscola:
    """Testes para renderização do resumo DRE/Escola no Excel."""

    def test_render_to_xls_com_resumo_dre_escola(self, resultado_escolha_service: Any) -> None:
        """Testa renderização Excel com resumo DRE/Escola.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        cargos_list = [{'codigo': '123', 'descricao': 'Professor', 'tipos_escolha': [], 'resumo_dre_escola': [{'nome': 'DRE Butantã', 'escolas': [{'nome': 'EMEF Teste', 'tipo_ue': 'EMEF', 'codigo_eol': '12345', 'qtd_vagas_definitivas': 5, 'qtd_vagas_precarias': 3, 'qtd_escolhas_definitivas': 2, 'qtd_escolhas_precarias': 1}]}]}]
        response = resultado_escolha_service.render_to_xls(cargos_list, 'Cabeçalho', '')
        assert isinstance(response, HttpResponse)
        assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in response['Content-Type']

    def test_render_to_xls_com_logo_url(self, resultado_escolha_service: Any) -> None:
        """Testa renderização Excel com logo via URL.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.context['usar_logotipo'] = True
        resultado_escolha_service.context['logo_url'] = 'http://example.com/logo.png'
        cargos_list = [{'codigo': '123', 'descricao': 'Professor', 'tipos_escolha': []}]
        with patch('relatorios.services.relatorios.resultado_escolha.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.content = b'fake_image_data'
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            response = resultado_escolha_service.render_to_xls(cargos_list, 'Cabeçalho', '')
        assert isinstance(response, HttpResponse)

    def test_render_to_xls_com_texto_final(self, resultado_escolha_service: Any) -> None:
        """Testa renderização Excel com texto final.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.context['texto_final'] = '<p>Texto final</p>'
        cargos_list = [{'codigo': '123', 'descricao': 'Professor', 'tipos_escolha': []}]
        response = resultado_escolha_service.render_to_xls(cargos_list, 'Cabeçalho', '')
        assert isinstance(response, HttpResponse)

class TestRenderToDocxResumoDreEscola:
    """Testes para renderização do resumo DRE/Escola no DOCX."""

    def test_render_to_docx_com_resumo_dre_escola(self, resultado_escolha_service: Any) -> None:
        """Testa renderização DOCX com resumo DRE/Escola.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        cargos_list = [{'codigo': '123', 'descricao': 'Professor', 'tipos_escolha': [], 'resumo_dre_escola': [{'nome': 'DRE Butantã', 'escolas': [{'nome': 'EMEF Teste', 'tipo_ue': 'EMEF', 'codigo_eol': '12345', 'qtd_vagas_definitivas': 5, 'qtd_vagas_precarias': 3, 'qtd_escolhas_definitivas': 2, 'qtd_escolhas_precarias': 1}]}]}]
        response = resultado_escolha_service.render_to_docx(cargos_list, 'Cabeçalho', 'Texto final')
        assert isinstance(response, HttpResponse)
        assert 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in response['Content-Type']

    def test_render_to_docx_com_texto_final(self, resultado_escolha_service: Any) -> None:
        """Testa renderização DOCX com texto final.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        cargos_list = [{'codigo': '123', 'descricao': 'Professor', 'tipos_escolha': []}]
        response = resultado_escolha_service.render_to_docx(cargos_list, 'Cabeçalho', '<p>Texto final</p>')
        assert isinstance(response, HttpResponse)

class TestTiposAntigosCompatibilidade:
    """Testes para compatibilidade com tipos antigos."""

    def test_gerar_tipo_resultado_escolha_sim(self, settings: Any, parametrizacao: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_candidatos_response: Any) -> None:
        """Testa geração com tipo antigo RESULTADO_ESCOLHA_SIM.
        
        Args:
            self: Instância do objeto.
            settings: Parâmetro settings da operação.
            parametrizacao: Parâmetro parametrizacao da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        config_antiga, _ = ConfiguracaoRelatorio.objects.get_or_create(tipo='RESULTADO_ESCOLHA_SIM', defaults={'usar_logotipo': False, 'cabecalho': '', 'texto_final': '', 'cabecalho_capa_ata': ''})
        settings.ESCOLHAS_API_URL = 'http://escolhas'
        settings.CANDIDATOS_API_URL = 'http://candidatos'
        settings.PROCESSOS_API_URL = 'http://processos'
        settings.AGENDAS_API_URL = 'http://agendas'
        service = ResultadoEscolha(tipo='RESULTADO_ESCOLHA_SIM', configuracao=config_antiga, parametrizacao=parametrizacao)
        service.processos_service = Mock()
        service.agendas_service = Mock()
        service.candidatos_service = Mock()
        service.escolhas_service = Mock()
        service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        service.escolhas_service.buscar_escolhas_por_candidatos.return_value = [{'candidato_uuid': 'candidato-uuid-1'}]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        service.escolhas_service.buscar_escolhas_por_candidatos.assert_called_once()
        call_args = service.escolhas_service.buscar_escolhas_por_candidatos.call_args
        assert call_args[1]['situacao'] == 'escolha'

    def test_render_to_xls_tipo_antigo(self, resultado_escolha_service: Any) -> None:
        """Testa renderização Excel com tipo antigo (sem tipos_escolha).
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.tipo = 'RESULTADO_ESCOLHA_SIM'
        cargos_list = [{'codigo': '123', 'descricao': 'Professor', 'agendas': [{'uuid': 'agenda-1', 'nome': 'Agenda 1', 'sessao': '1', 'candidatos': [{'nome': 'João', 'escolha': 'S'}]}]}]
        response = resultado_escolha_service.render_to_xls(cargos_list, 'Cabeçalho', '')
        assert isinstance(response, HttpResponse)

    def test_render_to_docx_tipo_antigo(self, resultado_escolha_service: Any) -> None:
        """Testa renderização DOCX com tipo antigo (sem tipos_escolha).
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.tipo = 'RESULTADO_ESCOLHA_SIM'
        cargos_list = [{'codigo': '123', 'descricao': 'Professor', 'agendas': [{'uuid': 'agenda-1', 'nome': 'Agenda 1', 'sessao': '1', 'candidatos': [{'nome': 'João', 'escolha': 'S'}]}]}]
        response = resultado_escolha_service.render_to_docx(cargos_list, 'Cabeçalho')
        assert isinstance(response, HttpResponse)

    def test_render_to_xls_logo_erro(self, resultado_escolha_service: Any) -> None:
        """Testa renderização Excel quando há erro ao processar logo.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.context['usar_logotipo'] = True
        resultado_escolha_service.context['logo_url'] = 'http://example.com/logo.png'
        cargos_list = [{'codigo': '123', 'descricao': 'Professor', 'tipos_escolha': []}]
        with patch('relatorios.services.relatorios.resultado_escolha.requests.get', side_effect=Exception('Erro')):
            response = resultado_escolha_service.render_to_xls(cargos_list, 'Cabeçalho', '')
        assert isinstance(response, HttpResponse)

    def test_render_to_xls_logo_arquivo_local(self, resultado_escolha_service: Any, tmp_path: Any) -> None:
        """Testa renderização Excel com logo de arquivo local.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            tmp_path: Parâmetro tmp path da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.context['usar_logotipo'] = True
        logo_file = tmp_path / 'logo.png'
        logo_file.write_bytes(b'fake_image')
        resultado_escolha_service.context['logo_url'] = str(logo_file)
        cargos_list = [{'codigo': '123', 'descricao': 'Professor', 'tipos_escolha': []}]
        response = resultado_escolha_service.render_to_xls(cargos_list, 'Cabeçalho', '')
        assert isinstance(response, HttpResponse)

    def test_render_to_xls_tipos_escolha_completo(self, resultado_escolha_service: Any) -> None:
        """Testa renderização Excel com estrutura completa de tipos_escolha.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        cargos_list = [{'codigo': '123', 'descricao': 'Professor', 'tipos_escolha': [{'nome': 'Escolha', 'agendas': [{'uuid': 'agenda-1', 'nome': 'Agenda 1', 'sessao': '1', 'candidatos': [{'classificacao_geral': 1, 'classificacao_nna': '-', 'classificacao_def': '-', 'nome': 'João', 'rg': '123', 'cpf': '123', 'escolha': 'S'}]}]}]}]
        response = resultado_escolha_service.render_to_xls(cargos_list, 'Cabeçalho', '')
        assert isinstance(response, HttpResponse)

    def test_render_to_docx_tipos_escolha_completo(self, resultado_escolha_service: Any) -> None:
        """Testa renderização DOCX com estrutura completa de tipos_escolha.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        cargos_list = [{'codigo': '123', 'descricao': 'Professor', 'tipos_escolha': [{'nome': 'Escolha', 'agendas': [{'uuid': 'agenda-1', 'nome': 'Agenda 1', 'sessao': '1', 'candidatos': [{'classificacao_geral': 1, 'classificacao_nna': '-', 'classificacao_def': '-', 'nome': 'João', 'rg': '123', 'cpf': '123', 'escolha': 'S'}]}]}]}]
        response = resultado_escolha_service.render_to_docx(cargos_list, 'Cabeçalho')
        assert isinstance(response, HttpResponse)

class TestIntegracaoCompleta:
    """Testes de integração completos."""

    def test_fluxo_completo_html(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_agendas_response: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa fluxo completo de geração HTML.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_agendas_response: Parâmetro mock agendas response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = mock_agendas_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        escolhas_com_situacao = [{**item, 'situacao': 'escolha'} if isinstance(item, dict) else item for item in mock_escolhas_response]
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.side_effect = [escolhas_com_situacao, [], []]
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')) as m_render:
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html', cabecalho='Teste')
        assert isinstance(response, HttpResponse)
        m_render.assert_called_once()
        assert isinstance(dados, list)
        if len(dados) > 0:
            assert 'codigo' in dados[0]
            assert 'descricao' in dados[0]
            assert 'tipos_escolha' in dados[0] or 'agendas' in dados[0]

    def test_fluxo_completo_com_agenda_por_cargo(self, resultado_escolha_service: Any, mock_cargos_response: Any, mock_candidatos_response: Any, mock_escolhas_response: Any) -> None:
        """Testa quando agenda é encontrada pelo cargo do candidato.
        
        Args:
            self: Instância do objeto.
            resultado_escolha_service: Parâmetro resultado escolha service da operação.
            mock_cargos_response: Parâmetro mock cargos response da operação.
            mock_candidatos_response: Parâmetro mock candidatos response da operação.
            mock_escolhas_response: Parâmetro mock escolhas response da operação.
        
        Returns:
            Não retorna valor.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        agenda_response = _MockResponse({'results': [{'uuid': 'agenda-uuid-1', 'cargo_codigo': '123', 'cargo_nome': 'Professor', 'candidatos_uuids': [], 'escolha_em': '2026-01-05', 'sessao': '1'}]})
        resultado_escolha_service.processos_service.buscar_cargos_por_processo.return_value = mock_cargos_response
        resultado_escolha_service.agendas_service.buscar_agendas.return_value = agenda_response
        resultado_escolha_service.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = mock_candidatos_response
        resultado_escolha_service.escolhas_service.buscar_escolhas_por_candidatos.return_value = mock_escolhas_response
        with patch('relatorios.services.relatorios.resultado_escolha.render', return_value=HttpResponse('OK')):
            with patch('relatorios.services.relatorios.resultado_escolha.timezone.now', return_value=datetime(2026, 1, 5, 12, 0, 0)):
                response, dados = resultado_escolha_service.gerar(processo_uuid='proc-123', request=_make_request(), formato='html')
        assert isinstance(response, HttpResponse)
        assert len(dados) > 0
