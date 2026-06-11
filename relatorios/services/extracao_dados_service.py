"""
Serviço de orquestração para extração de dados agregados de microserviços.
"""

import logging
from collections import defaultdict

from django.conf import settings
from requests import RequestException
from rest_framework.exceptions import NotFound

from relatorios.services.candidatos_api_service import CandidatosService
from relatorios.services.concurso_api_service import ConcursoService
from relatorios.services.escolhas_api_service import EscolhasService
from relatorios.services.processo_convocacao_api_service import (
    ProcessoConvocacaoService,
)

logger = logging.getLogger(__name__)


class ExtracaoDadosService:
    """Agrega dados de convocação, candidatos, escolhas e concursos."""

    def __init__(
        self,
        convocacao_base_url: str | None = None,
        candidatos_base_url: str | None = None,
        escolhas_base_url: str | None = None,
        concursos_base_url: str | None = None,
        timeout_seconds: int = 30,
    ):
        """Inicializa o serviço de extração de dados.

        Args:
            convocacao_base_url: URL base do microserviço de convocação
            candidatos_base_url: URL base do microserviço de candidatos
            escolhas_base_url: URL base do microserviço de escolhas
            concursos_base_url: URL base do microserviço de concursos
            timeout_seconds: Tempo limite em segundos para as requisições
        """
        convocacao_url = convocacao_base_url or settings.CONVOCACAO_API_URL
        candidatos_url = candidatos_base_url or settings.CANDIDATOS_API_URL
        escolhas_url = escolhas_base_url or settings.ESCOLHAS_API_URL
        concursos_url = concursos_base_url or settings.CONCURSOS_API_URL
        self.processo_service = ProcessoConvocacaoService(
            base_url=convocacao_url, timeout_seconds=timeout_seconds
        )
        self.candidatos_service = CandidatosService(
            base_url=candidatos_url, timeout_seconds=timeout_seconds
        )
        self.escolhas_service = EscolhasService(
            base_url=escolhas_url, timeout_seconds=timeout_seconds
        )
        self.concurso_service = ConcursoService(
            base_url=concursos_url, timeout_seconds=timeout_seconds
        )

    def extrair_todos(self) -> dict:
        """
        Extração geral sem filtros de concurso ou ano.

        Returns:
            Resposta agregada dos microserviços

        Raises:
            RequestException: Erro de comunicação com microserviços
        """
        return self._extrair_geral()

    def extrair(self, concurso_uuid: str, ano: int) -> dict:
        """
        Extração filtrada por concurso e ano.

        Args:
            concurso_uuid: UUID do concurso
            ano: Ano de referência YYYY

        Returns:
            Resposta agregada dos microserviços

        Raises:
            NotFound: Quando não há processos para o concurso/ano informados
            RequestException: Erro de comunicação com microserviços
        """
        return self._extrair_por_concurso(concurso_uuid=concurso_uuid, ano=ano)

    def _extrair_geral(self) -> dict:
        """Extração geral sem filtros de concurso ou ano.

        Returns:
            Resposta agregada dos microserviços

        Raises:
            RequestException: Erro de comunicação com microserviços
        """        
        candidatos_data = self.candidatos_service.buscar_extracao_dados()
        # candidatos_data = {
        #     "habilitados": {
        #         "total": 10000,
        #         "pcd": 50,
        #         "nna": 150,
        #         "geral": 9000
        #     },
        #     "convocados": 3000,
        #     "nao-convocados": 2000
        # }
        escolhas_data = self.escolhas_service.buscar_extracao_dados()
        # escolhas_data = {
        #     "escolha": 100,
        #     "reconvocacao": 200,
        #     "nao-escolha": 20,
        #     "dres": [
        #         {
        #             "nome": "DIRETORIA REGIONAL DE EDUCACAO SAO MIGUEL",
        #             "escolhas": 100,
        #             "vagas": 120
        #         },
        #         {
        #             "nome": "DIRETORIA REGIONAL DE EDUCACAO SAO MATEUS",
        #             "escolhas": 80,
        #             "vagas": 100
        #         },
        #         {
        #             "nome": "DIRETORIA REGIONAL DE EDUCACAO SANTO AMARO",
        #             "escolhas": 8,
        #             "vagas": 10
        #         },
        #         {
        #             "nome": "DIRETORIA REGIONAL DE EDUCACAO PIRITUBA/JARAGUA",
        #             "escolhas": 45,
        #             "vagas": 55
        #         },
        #         {
        #             "nome": "DIRETORIA REGIONAL DE EDUCACAO PENHA",
        #             "escolhas": 80,
        #             "vagas": 100
        #         },
        #         {
        #             "nome": "DIRETORIA REGIONAL DE EDUCACAO JACANA/TREMEMBE",
        #             "escolhas": 20,
        #             "vagas": 20
        #         },
        #         {
        #             "nome": "DIRETORIA REGIONAL DE EDUCACAO ITAQUERA",
        #             "escolhas": 115,
        #             "vagas": 120
        #         },
        #         {
        #             "nome": "DIRETORIA REGIONAL DE EDUCACAO GUAIANASES",
        #             "escolhas": 90,
        #             "vagas": 100
        #         },
        #         {
        #             "nome": "DIRETORIA REGIONAL DE EDUCACAO FREGUESIA/BRASILANDIA",
        #             "escolhas": 95,
        #             "vagas": 105
        #         },
        #         {
        #             "nome": "DIRETORIA REGIONAL DE EDUCACAO PINHEIROS",
        #             "escolhas": 82,
        #             "vagas": 97
        #         }
        #     ],
        #     "dres_concursos": {
        #         "46cce769-9180-463a-a6ff-43d320742bb7": [
        #             {
        #                 "nome": "DIRETORIA REGIONAL DE EDUCACAO SAO MIGUEL",
        #                 "escolhas": 100,
        #                 "vagas": 120,
        #                 "codigo_cargo": 1001,
        #                 "cargo_descricao": "Backend"
        #             },
        #             {
        #                 "nome": "DIRETORIA REGIONAL DE EDUCACAO SAO MATEUS",
        #                 "escolhas": 80,
        #                 "vagas": 100,
        #                 "codigo_cargo": 1002,
        #                 "cargo_descricao": "Frontend"
        #             },
        #             {
        #                 "nome": "DIRETORIA REGIONAL DE EDUCACAO SANTO AMARO",
        #                 "escolhas": 8,
        #                 "vagas": 10,
        #                 "codigo_cargo": 1003,
        #                 "cargo_descricao": "Mobile"
        #             },
        #             {
        #                 "nome": "DIRETORIA REGIONAL DE EDUCACAO PIRITUBA/JARAGUA",
        #                 "escolhas": 45,
        #                 "vagas": 55,
        #                 "codigo_cargo": 1001,
        #                 "cargo_descricao": "Backend"
        #             },
        #         ],
        #         "33646bd4-5410-455e-acde-7df18e02003b": [
        #             {
        #                 "nome": "DIRETORIA REGIONAL DE EDUCACAO SAO MIGUEL",
        #                 "escolhas": 100,
        #                 "vagas": 120,
        #                 "codigo_cargo": 1001,
        #                 "cargo_descricao": "Backend"
        #             },
        #             {
        #                 "nome": "DIRETORIA REGIONAL DE EDUCACAO SAO MATEUS",
        #                 "escolhas": 80,
        #                 "vagas": 100,
        #                 "codigo_cargo": 1002,
        #                 "cargo_descricao": "Frontend"
        #             },
        #             {
        #                 "nome": "DIRETORIA REGIONAL DE EDUCACAO SANTO AMARO",
        #                 "escolhas": 8,
        #                 "vagas": 10,
        #                 "codigo_cargo": 1003,
        #                 "cargo_descricao": "Mobile"
        #             },
        #             {
        #                 "nome": "DIRETORIA REGIONAL DE EDUCACAO PIRITUBA/JARAGUA",
        #                 "escolhas": 45,
        #                 "vagas": 55,
        #                 "codigo_cargo": 1001,
        #                 "cargo_descricao": "Backend"
        #             },
        #         ],
        #     }
        # }

        concurso_data = self.concurso_service.buscar_extracao_dados()
        # concurso_data = {
        #     "autorizacoes-publicadas": 100
        # }

        return {
            "candidatos": candidatos_data,
            "escolhas": escolhas_data,
            "concurso": concurso_data,
        }

    def _extrair_por_concurso(
        self, concurso_uuid: str, ano: int
    ) -> dict:
        """Extração filtrada por concurso e ano.

        Args:
            concurso_uuid: UUID do concurso
            ano: Ano de referência YYYY

        Returns:
            Resposta agregada dos microserviços

        Raises:
            NotFound: Quando não há processos para o concurso/ano informados
            RequestException: Erro de comunicação com microserviços
        """
        processos = self._buscar_processos(concurso_uuid)
        processos_por_ano = self._agrupar_processos_por_ano(processos)

        if ano not in processos_por_ano:
            raise NotFound(
                f"Nenhum processo de convocação encontrado para o ano {ano}."
            )

        filtros = [
            {"ano": ano_ref, "processo_uuids": uuids}
            for ano_ref, uuids in sorted(processos_por_ano.items())
        ]

        candidatos_data = (
            self.candidatos_service.buscar_extracao_dados(
                concurso_uuid=concurso_uuid,
                filtros=filtros,
            )
        )
        candidatos_data2 = {
            "habilitados": {
                "total": 10000,
                "pcd": 50,
                "nna": 150,
                "geral": 9000
            },
            "2026": {
                "convocados": 3000,
                "nao-convocados": 2000
            }
        }
        escolhas_data = self.escolhas_service.buscar_extracao_dados(
            concurso_uuid=concurso_uuid,
            filtros=filtros,
        )
        escolhas_data2 = {
            "2026": {
                "escolha": 100,
                "reconvocacao": 200,
                "nao-escolha": 20,
                "dres": [
                    {
                        "nome": "DIRETORIA REGIONAL DE EDUCACAO SAO MIGUEL",
                        "escolhas": 100,
                        "vagas": 120
                    },
                    {
                        "nome": "DIRETORIA REGIONAL DE EDUCACAO SAO MATEUS",
                        "escolhas": 80,
                        "vagas": 100
                    },
                    {
                        "nome": "DIRETORIA REGIONAL DE EDUCACAO SANTO AMARO",
                        "escolhas": 8,
                        "vagas": 10
                    },
                    {
                        "nome": "DIRETORIA REGIONAL DE EDUCACAO PIRITUBA/JARAGUA",
                        "escolhas": 45,
                        "vagas": 55
                    },
                    {
                        "nome": "DIRETORIA REGIONAL DE EDUCACAO PENHA",
                        "escolhas": 80,
                        "vagas": 100
                    },
                    {
                        "nome": "DIRETORIA REGIONAL DE EDUCACAO JACANA/TREMEMBE",
                        "escolhas": 20,
                        "vagas": 20
                    },
                    {
                        "nome": "DIRETORIA REGIONAL DE EDUCACAO ITAQUERA",
                        "escolhas": 115,
                        "vagas": 120
                    },
                    {
                        "nome": "DIRETORIA REGIONAL DE EDUCACAO GUAIANASES",
                        "escolhas": 90,
                        "vagas": 100
                    },
                    {
                        "nome": "DIRETORIA REGIONAL DE EDUCACAO FREGUESIA/BRASILANDIA",
                        "escolhas": 95,
                        "vagas": 105
                    },
                    {
                        "nome": "DIRETORIA REGIONAL DE EDUCACAO PINHEIROS",
                        "escolhas": 82,
                        "vagas": 97
                    }
                ]
            }
        }
        concurso_data = self.concurso_service.buscar_extracao_dados(
            concurso_uuid=concurso_uuid,
            ano=ano,
        )
        concurso_data2 = {
            "2026": {
                "autorizacoes-publicadas": 100
            }
        }

        return {
            "candidatos": candidatos_data,
            "escolhas": escolhas_data,
            "concurso": concurso_data,
        }

    def _buscar_processos(self, concurso_uuid: str) -> list[dict]:
        """Busca processos de convocação por concurso.

        Args:
            concurso_uuid: UUID do concurso

        Raises:
            NotFound: Quando não há processos para o concurso informado

        Returns:
            list[dict]: Lista de processos de convocação
        """        
        response = self.processo_service.buscar_processos_por_concurso(
            concurso_uuid
        )
        processos = self._extrair_lista(response.json())
        if not processos:
            raise NotFound(
                "Nenhum processo de convocação encontrado para o concurso "
                "informado."
            )
        return processos

    @staticmethod
    def _extrair_lista(data) -> list[dict]:
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
        return []

    @staticmethod
    def _agrupar_processos_por_ano(
        processos: list[dict],
    ) -> dict[int, list[str]]:
        """Agrupa processos de convocação por ano.

        Args:
            processos (list[dict]): Lista de processos de convocação

        Returns:
            dict[int, list[str]]: Dicionário com os anos como chaves e as listas de UUIDs dos processos como valores
        """
        processos_por_ano: dict[int, list[str]] = defaultdict(list)

        for processo in processos:
            processo_uuid = processo.get("uuid") or processo.get("id")
            if not processo_uuid:
                continue

            ano_processo = ExtracaoDadosService._obter_ano_processo(processo)
            if ano_processo is None:
                continue

            processos_por_ano[ano_processo].append(str(processo_uuid))

        return dict(processos_por_ano)

    @staticmethod
    def _obter_ano_processo(processo: dict) -> int | None:
        """Obtém o ano de um processo de convocação.

        Args:
            processo (dict): Processo de convocação

        Returns:
            int | None: Ano do processo de convocação
        """

        data_convocacao = processo.get("data_convocacao")
        if not data_convocacao:
            return None

        if isinstance(data_convocacao, str):
            return int(data_convocacao[:4])

        if hasattr(data_convocacao, "year"):
            return data_convocacao.year

        return None
