"""
Classe abstrata base para todos os tipos de relatórios.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
import re
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
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
    
    @staticmethod
    def processar_cabecalho_html(cabecalho: str) -> str:
        """
        Remove tags HTML do cabeçalho, preservando quebras de linha, espaçamento, tabs e margens.
        
        Args:
            cabecalho: String HTML com o cabeçalho
        
        Returns:
            String com o texto processado, sem tags HTML mas com formatação preservada
        """
        if not cabecalho:
            return ''
        
        # Primeiro, converte tags de quebra de linha para caracteres de nova linha
        cabecalho_texto = cabecalho
        # Converte <br>, <br/>, <br /> para quebra de linha
        cabecalho_texto = cabecalho_texto.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
        # Converte <p> e </p> para quebras de linha (parágrafos)
        cabecalho_texto = cabecalho_texto.replace('</p>', '\n').replace('<p>', '').replace('<p ', '<p>')
        # Remove outras tags HTML, mas preserva o texto e quebras de linha
        cabecalho_texto = strip_tags(cabecalho_texto)
        # Preserva espaços múltiplos e tabs (substitui &nbsp; por espaço se ainda houver)
        cabecalho_texto = cabecalho_texto.replace('&nbsp;', ' ')
        # Remove entidades HTML restantes
        cabecalho_texto = cabecalho_texto.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        cabecalho_texto = cabecalho_texto.replace('&quot;', '"').replace('&#39;', "'")
        # Limpa múltiplas quebras de linha consecutivas (mantém no máximo 2)
        cabecalho_texto = re.sub(r'\n{3,}', '\n\n', cabecalho_texto)
        # Remove espaços em branco no início e fim, mas preserva quebras de linha
        cabecalho_texto = cabecalho_texto.strip()
        
        return cabecalho_texto

