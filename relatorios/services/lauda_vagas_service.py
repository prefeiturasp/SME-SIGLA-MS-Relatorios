"""
Service para geração de relatório do tipo Lauda de Vagas.
"""

import logging

from django.conf import settings
from django.shortcuts import render

from relatorios.services.escolhas_api_service import EscolhasService

logger = logging.getLogger(__name__)


class LaudaVagasService:
    """
    Service responsável por gerar o relatório de Lauda de Vagas.
    """

    TEMPLATE_NAME = "relatorios/vagas_escolas.html"

    def __init__(self):
        self.escolhas_service = EscolhasService(
            base_url=settings.ESCOLHAS_API_URL
        )

    def gerar_relatorio(self, processo_uuid: str, request):
        """
        Gera o relatório de Lauda de Vagas.

        Args:
            processo_uuid: UUID do processo de convocação
            request: Objeto request do Django

        Returns:
            HttpResponse com o relatório gerado (HTML)
        """
        # Buscar vagas das escolas do microserviço de escolhas
        try:
            vagas_escolas = self.escolhas_service.buscar_vagas_escolas(
                processo_uuid=str(processo_uuid) if processo_uuid else "",
            )
        except Exception as exc:
            logger.error(
                "Falha ao buscar vagas de escolas da API externa: %s", exc
            )
            raise

        vagas = vagas_escolas.json().get("vagas", [])

        vagas_agrupadas = self._agrupar_vagas(vagas)

        cargos_list = self._preparar_dados_template(vagas_agrupadas)

        logger.info("Gerando HTML")
        return render(request, self.TEMPLATE_NAME, {"cargos": cargos_list})

    def _agrupar_vagas(self, vagas: list) -> dict:
        """
        Agrupa vagas por cargo_codigo e depois por DRE codigo.

        Args:
            vagas: Lista de vagas

        Returns:
            Dicionário agrupado por cargo e DRE
        """
        vagas_agrupadas = {}
        for vaga in vagas:
            cargo_codigo = vaga.get("cargo_codigo")
            dre_codigo = vaga.get("escola", {}).get("dre", {}).get("codigo")

            if cargo_codigo not in vagas_agrupadas:
                vagas_agrupadas[cargo_codigo] = {}

            if dre_codigo not in vagas_agrupadas[cargo_codigo]:
                vagas_agrupadas[cargo_codigo][dre_codigo] = []

            vagas_agrupadas[cargo_codigo][dre_codigo].append(vaga)

        return vagas_agrupadas

    def _preparar_dados_template(self, vagas_agrupadas: dict) -> list:
        """
        Prepara a estrutura de dados para o template.

        Args:
            vagas_agrupadas: Dicionário com vagas agrupadas por cargo e DRE

        Returns:
            Lista de cargos com suas DREs e vagas
        """
        cargos_list = []
        for cargo_codigo, dres in vagas_agrupadas.items():
            primeira_vaga = None
            for dre_codigo, vagas_list in dres.items():  # noqa: B007
                if vagas_list:
                    primeira_vaga = vagas_list[0]
                    break

            if primeira_vaga:
                dres_list = []
                for dre_codigo, vagas_list in dres.items():
                    if vagas_list:
                        primeira_vaga_dre = vagas_list[0]
                        dres_list.append(
                            {
                                "codigo": dre_codigo,
                                "nome": primeira_vaga_dre.get("escola", {})
                                .get("dre", {})
                                .get("nome", ""),
                                "vagas": vagas_list,
                            }
                        )

                cargos_list.append(
                    {
                        "codigo": cargo_codigo,
                        "descricao": primeira_vaga.get("cargo_descricao", ""),
                        "dres": dres_list,
                    }
                )

        return cargos_list
