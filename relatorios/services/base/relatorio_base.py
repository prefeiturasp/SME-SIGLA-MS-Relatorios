"""Classe abstrata base para todos os tipos de relatórios."""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from weasyprint import HTML

from .utils import ajustar_logo_caminho

logger = logging.getLogger(__name__)


class RelatorioBase(ABC):
    """Classe abstrata que define a interface comum para todos os tipos de."""

    def __init__(
        self, *, configuracao: Any, parametrizacao: Any, **kwargs: Any
    ) -> None:
        """Inicializa a instância com os parâmetros informados.

        Args:
            configuracao: Configuracao.
            parametrizacao: Parametrizacao.
            **kwargs: Argumentos nomeados repassados ao comando.
        """
        self.configuracao = configuracao
        self.parametrizacao = parametrizacao
        logo_url = ""
        if parametrizacao and parametrizacao.logo:
            try:
                logo_url = ajustar_logo_caminho(parametrizacao.logo.url) or ""
            except (ValueError, AttributeError):
                logo_url = ""
        self.context: dict[str, Any] = {
            "cabecalho": configuracao.cabecalho
            or configuracao.cabecalho_gabarito,
            "cabecalho_capa_ata": configuracao.cabecalho_capa_ata or "",
            "texto_final": configuracao.texto_final,
            "usar_logotipo": bool(configuracao.usar_logotipo),
            "logo_url": logo_url,
            "cabecalho_padrao": parametrizacao.cabecalho
            if parametrizacao
            else "",
        }

    @abstractmethod
    def gerar(
        self,
        processo_uuid: str,
        request: Any,
        formato: str = "html",
        **kwargs: Any,
    ) -> None:
        """Método abstrato que deve ser implementado por todas as classes.

        Args:
            processo_uuid: UUID do processo de convocação.
            request: Requisição HTTP recebida.
            formato: Formato.
            **kwargs: Argumentos nomeados repassados ao comando.

        Returns:
            Nenhum valor.
        """
        pass

    def render_to_pdf(
        self, template_name: Any, context: Any, filename: Any = "relatorio.pdf"
    ) -> Any:
        """Renderiza um template HTML para PDF usando WeasyPrint.

        Args:
            template_name: Template name.
            context: Dados de contexto usados na renderização.
            filename: Nome do arquivo gerado para download.

        Returns:
            Conteúdo textual gerado.
        """
        try:
            html_string = render_to_string(template_name, context)
            html = HTML(string=html_string, base_url="")
            pdf_buffer = BytesIO()
            html.write_pdf(
                pdf_buffer, optimize_images=True, presentational_hints=True
            )
            pdf_buffer.seek(0)
            response = HttpResponse(
                pdf_buffer.read(), content_type="application/pdf"
            )
            response["Content-Disposition"] = (
                f'attachment; filename="{filename}"'
            )
            return response
        except Exception as exc:
            logger.error("Erro ao gerar PDF: %s", exc, exc_info=True)
            raise

    @staticmethod
    def processar_cabecalho_html(cabecalho: str) -> str:
        """Processa cabecalho html.

        Args:
            cabecalho: Cabecalho.

        Returns:
            Conteúdo textual gerado.
        """
        if not cabecalho:
            return ""
        cabecalho_texto = cabecalho
        cabecalho_texto = (
            cabecalho_texto.replace("<br>", "\n")
            .replace("<br/>", "\n")
            .replace("<br />", "\n")
        )
        cabecalho_texto = (
            cabecalho_texto.replace("</p>", "\n")
            .replace("<p>", "")
            .replace("<p ", "<p>")
        )
        cabecalho_texto = strip_tags(cabecalho_texto)
        cabecalho_texto = cabecalho_texto.replace("&nbsp;", " ")
        cabecalho_texto = (
            cabecalho_texto.replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
        )
        cabecalho_texto = cabecalho_texto.replace("&quot;", '"').replace(
            "&#39;", "'"
        )
        cabecalho_texto = re.sub("\\n{3,}", "\n\n", cabecalho_texto)
        cabecalho_texto = cabecalho_texto.strip()
        return cabecalho_texto
