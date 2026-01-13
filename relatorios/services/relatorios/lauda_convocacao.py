"""
Implementação concreta do relatório de Lauda de Convocação.
"""
import json
import logging
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from relatorios.services.base.relatorio_base import RelatorioBase
from relatorios.services.lauda_convocacao_service import LaudaConvocacaoService

logger = logging.getLogger(__name__)


class LaudaConvocacao(RelatorioBase):
    """
    Classe concreta responsável por gerar o relatório de Lauda de Convocação.
    """
    
    TEMPLATE_NAME = 'relatorios/lauda_convocacao.html'
    
    def __init__(self):
        """Inicializa o service com as dependências necessárias."""
        self.lauda_service = LaudaConvocacaoService(
            candidatos_base_url=settings.CANDIDATOS_API_URL,
            processo_base_url=settings.CONVOCACAO_API_URL,
            agendas_base_url=settings.AGENDAS_API_URL
        )
    
    def gerar(self, processo_uuid: str, request, formato: str = 'html', cabecalho: str = ''):
        """
        Gera o relatório de Lauda de Convocação.
        
        Args:
            processo_uuid: UUID do processo de convocação
            request: Objeto request do Django
            formato: Formato do relatório ('html', 'pdf' ou 'xls')
            cabecalho: Texto do cabeçalho do relatório (opcional)
        
        Returns:
            Tupla (HttpResponse, dados) onde:
            - HttpResponse: resposta com o relatório gerado (HTML, PDF ou XLS)
            - dados: estrutura de dados do relatório para salvar no banco
        """
        # Processar lauda de convocação usando o serviço
        try:
            dados_lauda = self.lauda_service.processar_lauda_convocacao(
                processo_uuid=str(processo_uuid) if processo_uuid else ''
            )

        except Exception as exc:
            logger.error('Falha ao processar lauda de convocação: %s', exc)
            raise
        
        # Obter cabeçalho: prioriza o enviado no request; se vier vazio, usa o padrão do settings
        cabecalho_input = (cabecalho or '').strip()
        cabecalho_final = cabecalho_input if cabecalho_input else settings.RELATORIO_CABECALHO_PADRAO
        cabecalho_padrao = settings.RELATORIO_CABECALHO_PADRAO

        if formato == 'pdf':
            filename = f'lauda_convocacao_{processo_uuid}.pdf'
            logger.info('Gerando PDF: %s', filename)
            context = {
                'cargos': dados_lauda.get('cargos', []),
                'cabecalho': cabecalho_final,
                'cabecalho_padrao': cabecalho_padrao
            }
            response = self.render_to_pdf(
                self.TEMPLATE_NAME,
                context,
                filename=filename
            )
            return response, dados_lauda
        elif formato == 'html':
            logger.info('Gerando HTML')
            context = {
                'cargos': dados_lauda.get('cargos', []),
                'cabecalho': cabecalho_final,
                'cabecalho_padrao': cabecalho_padrao
            }
            response = render(
                request,
                self.TEMPLATE_NAME,
                context
            )
            return response, dados_lauda
        else:
            # Retornar JSON por padrão
            response = JsonResponse(dados_lauda, safe=False)
        
        return response, dados_lauda
