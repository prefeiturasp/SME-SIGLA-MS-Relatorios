"""
Serviço de orquestração para extração de dados agregados de microserviços.
"""

import logging
import re
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

_DRE_NOME_REGEX = re.compile(
    r"diretoria\s+regional\s+de\s+educa[cç][aã]o",
    re.IGNORECASE,
)


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

    def extrair_total(self) -> dict:
        """
        Extração total de dados.

        Returns:
            Resposta agregada dos microserviços

        Raises:
            RequestException: Erro de comunicação com microserviços
        """
        return self._extrair_total()

    def extrair(self, concurso_uuid: str, anos: list[int]) -> dict:
        """
        Extração filtrada por concurso e anos.

        Args:
            concurso_uuid: UUID do concurso
            anos: Anos de referência YYYY (1 ou 2)

        Returns:
            Resposta agregada dos microserviços

        Raises:
            NotFound: Quando não há processos para o concurso/anos informados
            RequestException: Erro de comunicação com microserviços
        """
        return self._extrair_por_concurso(
            concurso_uuid=concurso_uuid, anos=anos
        )

    def _extrair_total(self) -> dict:
        """Extração total de dados sem filtrar por concurso ou ano.

        Returns:
            dict: Dicionário com os dados de extração de cada microserviço

        Raises:
            RequestException: Erro de comunicação com microserviços
        """
        candidatos_data = self.candidatos_service.buscar_extracao_dados()
        escolhas_data = self.escolhas_service.buscar_extracao_dados()
        concurso_data = self.concurso_service.buscar_extracao_dados()

        return {
            "candidatos": candidatos_data,
            "escolhas": escolhas_data,
            "concurso": concurso_data,
        }

    def _extrair_por_concurso(
        self, concurso_uuid: str, anos: list[int]
    ) -> dict:
        """Extração filtrada por concurso e anos.

        Args:
            concurso_uuid: UUID do concurso
            anos: Anos de referência YYYY (1 ou 2)

        Returns:
            Resposta agregada dos microserviços

        Raises:
            NotFound: Quando não há processos para o concurso/anos informados
            RequestException: Erro de comunicação com microserviços
        """
        anos_ordenados = sorted(anos)
        processos = self._buscar_processos(concurso_uuid)
        processos_por_ano = self._agrupar_processos_por_ano(processos)

        anos_sem_processo = [
            ano for ano in anos_ordenados if ano not in processos_por_ano
        ]
        if anos_sem_processo:
            anos_fmt = ", ".join(str(ano) for ano in anos_sem_processo)
            raise NotFound(
                f"Nenhum processo de convocação encontrado para o(s) ano(s) "
                f"{anos_fmt}."
            )

        filtros_concurso = [
            {"ano": ano_ref, "processo_uuids": uuids}
            for ano_ref, uuids in sorted(processos_por_ano.items())
        ]
        filtros_selecionados = [
            {"ano": ano, "processo_uuids": processos_por_ano[ano]}
            for ano in anos_ordenados
        ]

        candidatos_data = self.candidatos_service.buscar_extracao_dados(
            concurso_uuid=concurso_uuid,
            filtros=filtros_selecionados,
        )
        escolhas_data = self.escolhas_service.buscar_extracao_dados(
            concurso_uuid=concurso_uuid,
            filtros=filtros_selecionados,
        )
        concurso_data = self.concurso_service.buscar_extracao_dados(
            concurso_uuid=concurso_uuid,
            anos=anos_ordenados,
        )

        resultado = {
            "concurso_uuid": concurso_uuid,
            "filtros": filtros_concurso,
            "candidatos": candidatos_data,
            "escolhas": escolhas_data,
            "concurso": concurso_data,
        }

        if len(anos_ordenados) == 2:
            resultado["comparativo"] = self._montar_comparativo(
                anos=anos_ordenados,
                candidatos_data=candidatos_data,
                escolhas_data=escolhas_data,
                concurso_data=concurso_data,
            )

        return resultado

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
        """Extrai a lista de processos de convocação."""
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
            dict[int, list[str]]: Dicionário com os anos como chaves e as
            listas de UUIDs dos processos como valores
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

    @staticmethod
    def _diferenca_absoluta(
        valor_antigo: int | float, valor_recente: int | float
    ) -> int | float:
        return round(valor_recente - valor_antigo, 1)

    @staticmethod
    def _obter_valor(dados: dict | None, chave: str, padrao: int = 0) -> int:
        if not isinstance(dados, dict):
            return padrao
        valor = dados.get(chave, padrao)
        return int(valor) if valor is not None else padrao

    @staticmethod
    def _percentual_preenchimento(escolhas: int, vagas: int) -> float:
        if vagas <= 0:
            return 0.0
        return round((escolhas / vagas) * 100, 1)

    @staticmethod
    def _chave_dre(nome: str) -> str:
        chave = _DRE_NOME_REGEX.sub("DRE", nome)
        chave = re.sub(r"\s+", " ", chave).strip()
        return re.sub(r"^DRE\s+", "", chave, flags=re.IGNORECASE).strip()

    @classmethod
    def _obter_dres_por_chave(
        cls, escolhas_data: dict, ano: int
    ) -> dict[str, dict]:
        ano_data = escolhas_data.get(str(ano), {})
        dres = ano_data.get("dres", []) if isinstance(ano_data, dict) else []
        return {
            cls._chave_dre(dre.get("nome", "")): dre
            for dre in dres
            if isinstance(dre, dict) and dre.get("nome")
        }

    @classmethod
    def _montar_comparativo(
        cls,
        anos: list[int],
        candidatos_data: dict,
        escolhas_data: dict,
        concurso_data: dict,
    ) -> dict:
        ano_antigo, ano_recente = anos[0], anos[1]

        candidatos_antigo = candidatos_data.get(str(ano_antigo), {})
        candidatos_recente = candidatos_data.get(str(ano_recente), {})
        escolhas_antigo = escolhas_data.get(str(ano_antigo), {})
        escolhas_recente = escolhas_data.get(str(ano_recente), {})
        concurso_antigo = concurso_data.get(str(ano_antigo), {})
        concurso_recente = concurso_data.get(str(ano_recente), {})

        indicadores = {
            "convocados": cls._diferenca_absoluta(
                cls._obter_valor(candidatos_antigo, "convocados"),
                cls._obter_valor(candidatos_recente, "convocados"),
            ),
            "naoConvocados": cls._diferenca_absoluta(
                cls._obter_valor(candidatos_antigo, "nao-convocados"),
                cls._obter_valor(candidatos_recente, "nao-convocados"),
            ),
            "escolhasRealizadas": cls._diferenca_absoluta(
                cls._obter_valor(escolhas_antigo, "escolha"),
                cls._obter_valor(escolhas_recente, "escolha"),
            ),
            "reconvocacoes": cls._diferenca_absoluta(
                cls._obter_valor(escolhas_antigo, "reconvocacao"),
                cls._obter_valor(escolhas_recente, "reconvocacao"),
            ),
            "semEscolha": cls._diferenca_absoluta(
                cls._obter_valor(escolhas_antigo, "nao-escolha"),
                cls._obter_valor(escolhas_recente, "nao-escolha"),
            ),
            "autorizacoes": cls._diferenca_absoluta(
                cls._obter_valor(
                    concurso_antigo, "autorizacoes-publicadas"
                ),
                cls._obter_valor(
                    concurso_recente, "autorizacoes-publicadas"
                ),
            ),
        }

        dres_antigo = cls._obter_dres_por_chave(escolhas_data, ano_antigo)
        dres_recente = cls._obter_dres_por_chave(escolhas_data, ano_recente)
        dres_comparativo = {}

        for chave in sorted(set(dres_antigo) | set(dres_recente)):
            dre_antigo = dres_antigo.get(chave, {})
            dre_recente = dres_recente.get(chave, {})

            escolhas_a = cls._obter_valor(dre_antigo, "escolhas")
            escolhas_r = cls._obter_valor(dre_recente, "escolhas")
            vagas_a = cls._obter_valor(dre_antigo, "vagas")
            vagas_r = cls._obter_valor(dre_recente, "vagas")

            percentual_a = cls._percentual_preenchimento(escolhas_a, vagas_a)
            percentual_r = cls._percentual_preenchimento(escolhas_r, vagas_r)

            dres_comparativo[chave] = {
                "escolhas": cls._diferenca_absoluta(
                    escolhas_a, escolhas_r
                ),
                "vagas": cls._diferenca_absoluta(vagas_a, vagas_r),
                "percentualPreenchimento": cls._diferenca_absoluta(
                    percentual_a, percentual_r
                ),
            }

        return {
            "anos": anos,
            "indicadores": indicadores,
            "dres": dres_comparativo,
        }
