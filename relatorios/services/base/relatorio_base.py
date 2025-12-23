"""
Classe abstrata base para todos os tipos de relatórios.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class RelatorioBase(ABC):
    """
    Classe abstrata que define a interface comum para todos os tipos de relatórios.
    """
    
    @abstractmethod
    def gerar(self, processo_uuid: str, request, formato: str = 'html', cabecalho: str = ''):
        """
        Método abstrato que deve ser implementado por todas as classes filhas.
        
        Args:
            processo_uuid: UUID do processo de convocação
            request: Objeto request do Django
            formato: Formato do relatório ('html', 'pdf' ou 'xls')
            cabecalho: Texto do cabeçalho do relatório (opcional)
        
        Returns:
            Tupla (HttpResponse, dados) onde:
            - HttpResponse: resposta com o relatório gerado (HTML, PDF ou XLS)
            - dados: estrutura de dados do relatório para salvar no banco
        
        Raises:
            NotImplementedError: Se o método não for implementado pela classe filha
        """
        pass
    
    def render_to_pdf(self, template_name, context, filename='relatorio.pdf'):
        """
        Renderiza um template HTML para PDF usando WeasyPrint.
        Método disponível para todas as classes filhas.
        
        Args:
            template_name: Nome do template (ex: 'relatorios/vagas_escolas.html')
            context: Dicionário com o contexto do template
            filename: Nome do arquivo PDF gerado
        
        Returns:
            HttpResponse com o PDF gerado
        """
        try:
            # Renderizar template HTML
            html_string = render_to_string(template_name, context)
            
            # Gerar PDF a partir do HTML
            # Usar base_url vazio para evitar problemas com recursos externos
            html = HTML(string=html_string, base_url='')
            pdf_buffer = BytesIO()
            
            # Opções para melhor compatibilidade e controle de páginas
            html.write_pdf(
                pdf_buffer,
                optimize_images=True,
                presentational_hints=True
            )
            pdf_buffer.seek(0)
            
            # Criar resposta HTTP com o PDF
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as exc:
            logger.error('Erro ao gerar PDF: %s', exc, exc_info=True)
            raise

