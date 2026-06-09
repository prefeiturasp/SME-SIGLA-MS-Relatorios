"""Serviço para geração de lauda de convocação."""

from __future__ import annotations

import logging
from typing import Any

from requests import RequestException
from sigla_sdk.context import get_correlation_id

from .agendas_api_service import AgendasService
from .candidatos_api_service import CandidatosService
from .escolhas_api_service import EscolhasService
from .processo_convocacao_api_service import ProcessoConvocacaoService

logger = logging.getLogger(__name__)


class LaudaConvocacaoService:
    """Serviço para geração de lauda de convocação."""

    def __init__(
        self,
        candidatos_base_url: str = "https://example.com",
        processo_base_url: str = "https://example.com",
        agendas_base_url: str = "https://example.com",
        escolhas_base_url: str = "https://example.com",
        timeout_seconds: int = 30,
    ) -> None:
        """Inicializa o serviço de lauda de convocação.

        Args:
            self: Instância do objeto.
            candidatos_base_url: URL base da API de candidatos.
            processo_base_url: URL base da API de processos de convocação.
            agendas_base_url: URL base da API de agendas.
            escolhas_base_url: URL base da API de escolhas.
            timeout_seconds: Timeout em segundos para as requisições.

        Raises:
            Nenhuma exceção específica documentada.
        """
        self.candidatos_service = CandidatosService(
            base_url=candidatos_base_url, timeout_seconds=timeout_seconds
        )
        self.processo_service = ProcessoConvocacaoService(
            base_url=processo_base_url, timeout_seconds=timeout_seconds
        )
        self.agendas_service = AgendasService(
            base_url=agendas_base_url, timeout_seconds=timeout_seconds
        )
        self.escolhas_service = EscolhasService(
            base_url=escolhas_base_url, timeout_seconds=timeout_seconds
        )

    def _identificar_lacunas(self, classificacoes: list[int]) -> list[int]:
        """Identifica lacunas em uma lista de classificações.

        Args:
            self: Instância do objeto.
            classificacoes: Lista de classificações (pode conter None).

        Returns:
            Lista com os registros resultantes.

        Raises:
            Nenhuma exceção específica documentada.
        """
        classificacoes_validas = sorted(
            set(
                c
                for c in classificacoes
                if c is not None and isinstance(c, int)
            )
        )
        if not classificacoes_validas:
            return []
        min_class = min(classificacoes_validas)
        max_class = max(classificacoes_validas)
        todas_classificacoes = set(range(min_class, max_class + 1))
        lacunas = sorted(todas_classificacoes - set(classificacoes_validas))
        return lacunas

    def _separar_por_tipo(
        self, candidatos: list[dict]
    ) -> dict[str, list[dict]]:
        """Separa candidatos por tipo usando o campo categoria_efetiva: GERAL,.

        Args:
            self: Instância do objeto.
            candidatos: Lista de candidatos retornados da API.

        Returns:
            Dicionário com os dados processados.

        Raises:
            Nenhuma exceção específica documentada.
        """
        separados = {"geral": [], "nna": [], "pcd": []}  # type: ignore[var-annotated]
        for candidato in candidatos:
            categoria_efetiva = candidato.get("categoria_efetiva")
            if categoria_efetiva == "GERAL":
                separados["geral"].append(candidato)
            elif categoria_efetiva == "NNA":
                separados["nna"].append(candidato)
            elif categoria_efetiva == "PCD":
                separados["pcd"].append(candidato)
        return separados

    def _extrair_classificacoes(
        self, candidatos: list[dict], campo: str
    ) -> list[int]:
        """Extrai classificações de uma lista de candidatos.

        Args:
            self: Instância do objeto.
            candidatos: Lista de candidatos.
            campo: Nome do campo de classificação ('classificacao',.

        Returns:
            Lista com os registros resultantes.

        Raises:
            Nenhuma exceção específica documentada.
        """
        return [candidato.get(campo) for candidato in candidatos]  # type: ignore[misc]

    def _buscar_candidatos_faltantes(
        self,
        outros_processos_uuid: list[str],
        lacunas_geral: list[int],
        lacunas_nna: list[int],
        lacunas_pcd: list[int],
        codigo_cargo: list[str] | str | None = None,
        ordering: str = "ranking_escolha",
    ) -> dict[str, list[dict]]:
        """Busca candidatos faltantes nos outros processos do mesmo concurso,.

        Args:
            self: Instância do objeto.
            outros_processos_uuid: Lista de UUIDs dos outros processos.
            lacunas_geral: Lista de classificações faltantes (Geral).
            lacunas_nna: Lista de classificações faltantes (NNA).
            lacunas_pcd: Lista de classificações faltantes (PCD).
            codigo_cargo: Código(s) do cargo para filtrar (opcional).
            ordering: Campo para ordenação.

        Returns:
            Dicionário com os dados processados.

        Raises:
            Nenhuma exceção específica documentada.
        """
        candidatos_faltantes = {"geral": [], "nna": [], "pcd": []}  # type: ignore[var-annotated]
        if not outros_processos_uuid:
            return candidatos_faltantes
        try:
            if lacunas_geral:
                logger.info(
                    "Buscando candidatos Gerais faltantes (classificações: %s) nos processos: %s",  # noqa: E501
                    lacunas_geral,
                    outros_processos_uuid,
                )
                response_geral = self.candidatos_service.buscar_habilitados_por_processos_e_classificacoes(  # noqa: E501
                    processo_uuids=outros_processos_uuid,
                    classificacao=lacunas_geral,
                    codigo_cargo=codigo_cargo,
                    ordering=ordering,
                )
                candidatos_geral_data = response_geral.json()
                if isinstance(candidatos_geral_data, list):
                    candidatos_faltantes["geral"] = candidatos_geral_data
                else:
                    candidatos_faltantes["geral"] = []
                candidatos_uuids = [
                    str(c.get("uuid"))
                    for c in candidatos_faltantes["geral"]
                    if c.get("uuid") is not None
                ]
                reconvocacao_uuids: set[str] = set()
                if candidatos_uuids:
                    escolhas_reconvocacao = (
                        self.escolhas_service.buscar_escolhas_por_candidatos(
                            candidato_uuids=candidatos_uuids,
                            situacao="reconvocacao",
                        )
                    )
                    reconvocacao_uuids = set(
                        str(e.get("candidato_uuid"))
                        for e in escolhas_reconvocacao or []
                        if e.get("candidato_uuid") is not None
                    )
                for candidato in candidatos_faltantes["geral"]:
                    status_especial = (
                        "JÁ CONVOCADO - LEI 13.398/02"
                        if candidato.get("classificacao_nna") is not None
                        else "JÁ CONVOCADO - LEI 15.939/13"
                        if candidato.get("classificacao_pcd") is not None
                        else ""
                    )
                    if str(candidato.get("uuid")) in reconvocacao_uuids:
                        status_especial = (
                            f"{status_especial} - OPTOU POR RECONVOCAÇÃO"
                            if status_especial
                            else "OPTOU POR RECONVOCAÇÃO"
                        )
                    candidato["status_especial"] = status_especial
                logger.info(
                    "Encontrados %d candidatos Gerais faltantes",
                    len(candidatos_faltantes["geral"]),
                )
            if lacunas_nna:
                logger.info(
                    "Buscando candidatos NNA faltantes (classificações: %s) nos processos: %s",  # noqa: E501
                    lacunas_nna,
                    outros_processos_uuid,
                )
                response_nna = self.candidatos_service.buscar_habilitados_por_processos_e_classificacoes(  # noqa: E501
                    processo_uuids=outros_processos_uuid,
                    classificacao_nna=lacunas_nna,
                    codigo_cargo=codigo_cargo,
                    ordering=ordering,
                )
                candidatos_nna_data = response_nna.json()
                if isinstance(candidatos_nna_data, list):
                    candidatos_faltantes["nna"] = candidatos_nna_data
                else:
                    candidatos_faltantes["nna"] = []
                candidatos_uuids = [
                    str(c.get("uuid"))
                    for c in candidatos_faltantes["nna"]
                    if c.get("uuid") is not None
                ]
                reconvocacao_uuids: set[str] = set()  # type: ignore[no-redef]
                if candidatos_uuids:
                    try:
                        escolhas_reconvocacao = self.escolhas_service.buscar_escolhas_por_candidatos(  # noqa: E501
                            candidato_uuids=candidatos_uuids,
                            situacao="reconvocacao",
                        )
                        reconvocacao_uuids = set(
                            str(e.get("candidato_uuid"))
                            for e in escolhas_reconvocacao or []
                            if e.get("candidato_uuid") is not None
                        )
                    except RequestException:
                        logger.exception(
                            "Erro ao buscar escolhas (reconvocacao) para candidatos NNA faltantes",  # noqa: E501
                            extra={
                                "correlation_id": get_correlation_id(),
                                "candidatos_uuids_count": len(
                                    candidatos_uuids
                                ),
                            },
                        )
                for candidato in candidatos_faltantes["nna"]:
                    status_especial = "CANDIDATOS JÁ CLASSIFICADO."
                    if str(candidato.get("uuid")) in reconvocacao_uuids:
                        status_especial = (
                            f"{status_especial} - OPTOU POR RECONVOCAÇÃO"
                        )
                    candidato["status_especial"] = status_especial
                logger.info(
                    "Encontrados %d candidatos NNA faltantes",
                    len(candidatos_faltantes["nna"]),
                )
            if lacunas_pcd:
                logger.info(
                    "Buscando candidatos PCD faltantes (classificações: %s) nos processos: %s",  # noqa: E501
                    lacunas_pcd,
                    outros_processos_uuid,
                )
                todos_candidatos_pcd = []
                for processo_uuid in outros_processos_uuid:
                    try:
                        response_pcd = (
                            self.candidatos_service.buscar_habilitados(
                                processo_uuid=processo_uuid, ordering=ordering
                            )
                        )
                        candidatos_pcd_data = response_pcd.json()
                        if isinstance(candidatos_pcd_data, list):
                            todos_candidatos_pcd.extend(candidatos_pcd_data)
                    except RequestException as exc:
                        logger.warning(
                            "Erro ao buscar candidatos do processo %s: %s",
                            processo_uuid,
                            exc,
                        )
                candidatos_faltantes["pcd"] = [
                    c
                    for c in todos_candidatos_pcd
                    if c.get("classificacao_pcd") is not None
                    and c.get("classificacao_pcd") in lacunas_pcd
                ]
                candidatos_uuids = [
                    str(c.get("uuid"))
                    for c in candidatos_faltantes["pcd"]
                    if c.get("uuid") is not None
                ]
                reconvocacao_uuids: set[str] = set()  # type: ignore[no-redef]
                if candidatos_uuids:
                    try:
                        escolhas_reconvocacao = self.escolhas_service.buscar_escolhas_por_candidatos(  # noqa: E501
                            candidato_uuids=candidatos_uuids,
                            situacao="reconvocacao",
                        )
                        reconvocacao_uuids = set(
                            str(e.get("candidato_uuid"))
                            for e in escolhas_reconvocacao or []
                            if e.get("candidato_uuid") is not None
                        )
                    except RequestException:
                        logger.exception(
                            "Erro ao buscar escolhas (reconvocacao) para candidatos PCD faltantes",  # noqa: E501
                            extra={
                                "correlation_id": get_correlation_id(),
                                "candidatos_uuids_count": len(
                                    candidatos_uuids
                                ),
                            },
                        )
                for candidato in candidatos_faltantes["pcd"]:
                    status_especial = "CANDIDATOS JÁ CLASSIFICADO."
                    if str(candidato.get("uuid")) in reconvocacao_uuids:
                        status_especial = (
                            f"{status_especial} - OPTOU POR RECONVOCAÇÃO"
                        )
                    candidato["status_especial"] = status_especial
                logger.info(
                    "Encontrados %d candidatos PCD faltantes",
                    len(candidatos_faltantes["pcd"]),
                )
        except RequestException as exc:
            logger.warning(
                "Erro ao buscar candidatos faltantes nos outros processos: %s",
                exc,
            )
        return candidatos_faltantes

    def _inserir_reclassificados_em_segmento(
        self,
        lista_segmento: list[dict],
        reclassificados: list[dict],
        cargo_codigo: Any,
        classificacao_attr: str,
    ) -> None:
        """Insere, dentro de lista_segmento, candidatos reclassificados.

        Args:
            self: Instância do objeto.
            lista_segmento: Parâmetro lista segmento.
            reclassificados: Parâmetro reclassificados.
            cargo_codigo: Parâmetro cargo codigo.
            classificacao_attr: Parâmetro classificacao attr.

        Returns:
            Não retorna valor.

        Raises:
            Nenhuma exceção específica documentada.
        """
        try:
            if (
                not isinstance(reclassificados, list)
                or not reclassificados
                or (not lista_segmento)
            ):
                return
            reclass_filtrados = [
                r
                for r in reclassificados
                if str(r.get("codigo_cargo")) == str(cargo_codigo)
                and isinstance(r.get(classificacao_attr), int)
            ]
            if not reclass_filtrados:
                return
            existentes: set[str] = set(
                [
                    str(item.get("uuid"))
                    for item in lista_segmento
                    if item.get("uuid")
                ]
            )
            j = 0
            while j < len(lista_segmento):
                cand = lista_segmento[j]
                cand_class = cand.get(classificacao_attr)
                if isinstance(cand_class, int):
                    candidatos_para_inserir = [
                        r
                        for r in reclass_filtrados
                        if r.get(classificacao_attr) < cand_class
                        and str(r.get("uuid")) not in existentes
                    ]  # type: ignore[operator]
                    candidatos_para_inserir.sort(
                        key=lambda x: x.get(classificacao_attr)
                    )  # type: ignore[arg-type,return-value]
                    for r in candidatos_para_inserir:
                        copia = dict(r)
                        copia["status_especial"] = (
                            "Utilizar classificação GERAL"
                        )
                        copia["foi_reclassificado"] = True
                        lista_segmento.insert(j, copia)
                        existentes.add(str(r.get("uuid")))
                        j += 1
                j += 1
        except Exception:
            return

    def _inserir_eliminados_em_segmento(
        self,
        lista_segmento: list[dict],
        eliminados: list[dict],
        cargo_codigo: Any,
        classificacao_attr: str,
    ) -> None:
        """Insere, dentro de lista_segmento, candidatos ELIMINADOS antes dos.

        Args:
            self: Instância do objeto.
            lista_segmento: Parâmetro lista segmento.
            eliminados: Parâmetro eliminados.
            cargo_codigo: Parâmetro cargo codigo.
            classificacao_attr: Parâmetro classificacao attr.

        Returns:
            Não retorna valor.

        Raises:
            Nenhuma exceção específica documentada.
        """
        try:
            if (
                not isinstance(eliminados, list)
                or not eliminados
                or (not lista_segmento)
            ):
                return
            elim_filtrados = []
            for r in eliminados:
                if str(r.get("codigo_cargo")) != str(cargo_codigo):
                    continue
                if classificacao_attr == "classificacao" and (
                    r.get("classificacao_nna") is not None
                    or r.get("classificacao_pcd") is not None
                ):
                    continue
                if isinstance(r.get(classificacao_attr), int):
                    elim_filtrados.append(r)
            if not elim_filtrados:
                return
            existentes: set[str] = set(
                [
                    str(item.get("uuid"))
                    for item in lista_segmento
                    if item.get("uuid")
                ]
            )
            j = 0
            while j < len(lista_segmento):
                cand = lista_segmento[j]
                cand_class = cand.get(classificacao_attr)
                if not isinstance(cand_class, int):
                    j += 1
                    continue
                candidatos_para_inserir = []
                for r in elim_filtrados:
                    if (
                        r.get("categoria_efetiva")
                        == cand.get("categoria_efetiva")
                        and (not cand.get("foi_reclassificado", False))
                        and (not r.get("foi_eliminado", False))
                        and (r.get(classificacao_attr) < cand_class)
                        and (str(r.get("uuid")) not in existentes)
                    ):  # type: ignore[operator]
                        r["foi_eliminado"] = True
                        candidatos_para_inserir.append(r)
                candidatos_para_inserir.sort(
                    key=lambda x: x.get(classificacao_attr)
                )  # type: ignore[arg-type,return-value]
                for r in candidatos_para_inserir:
                    copia = dict(r)
                    copia["status_especial"] = "Eliminado do certame"
                    lista_segmento.insert(j, copia)
                    existentes.add(str(r.get("uuid")))
                    j += 1
                j += 1
        except Exception:
            return

    def processar_lauda_convocacao(
        self, processo_uuid: str, ordering: str = "ranking_escolha"
    ) -> dict:
        """Processa a lauda de convocação para um processo.

        Args:
            self: Instância do objeto.
            processo_uuid: UUID do processo de convocação.
            ordering: Campo para ordenação (padrão: 'ranking_escolha').

        Returns:
            Dicionário com os dados processados.

        Raises:
            Nenhuma exceção específica documentada.
        """
        try:
            logger.info(
                "Buscando agendas para processo_uuid=%s", processo_uuid
            )
            response_agendas = self.agendas_service.buscar_agendas(
                processo_convocacao_uuid=processo_uuid,
                page=1,
                page_size=1000000,
            )
            agendas_data_temp = response_agendas.json()
            if (
                isinstance(agendas_data_temp, dict)
                and "results" in agendas_data_temp
            ):
                agendas_temp = agendas_data_temp["results"]
            elif isinstance(agendas_data_temp, list):
                agendas_temp = agendas_data_temp
            else:
                agendas_temp = []
            codigos_cargo = []
            for agenda in agendas_temp:
                cargo_codigo = agenda.get("cargo_codigo")
                if cargo_codigo and cargo_codigo not in codigos_cargo:
                    codigos_cargo.append(cargo_codigo)
            codigo_cargo_param = (
                codigos_cargo[0]
                if len(codigos_cargo) == 1
                else codigos_cargo
                if codigos_cargo
                else None
            )
            logger.info(
                "Códigos de cargo extraídos das agendas: %s",
                codigo_cargo_param,
            )
            resultado = {"processo_uuid": processo_uuid, "concurso_uuid": None}
            processo_uuid_principal = None
            outros_processos_uuid = []  # type: ignore[var-annotated]
            agendas_data = response_agendas.json()
            if isinstance(agendas_data, dict) and "results" in agendas_data:
                agendas = agendas_data["results"]
            elif isinstance(agendas_data, list):
                agendas = agendas_data
            else:
                agendas = []
            agendas_por_cargo = {}
            for agenda in agendas:
                cargo_nome = agenda.get("cargo_nome", "Sem Cargo")
                cargo_codigo = agenda.get("cargo_codigo")
                if cargo_codigo not in agendas_por_cargo:
                    agendas_por_cargo[cargo_codigo] = {
                        "cargo_nome": cargo_nome,
                        "cargo_codigo": cargo_codigo,
                        "agendas": [],
                    }
                agendas_por_cargo[cargo_codigo]["agendas"].append(agenda)
                if (
                    not agendas_por_cargo[cargo_codigo]["cargo_codigo"]
                    and cargo_codigo
                ):
                    agendas_por_cargo[cargo_codigo]["cargo_codigo"] = (
                        cargo_codigo
                    )
            logger.info(
                "Agendas agrupadas por cargo: %s",
                {
                    cargo: len(info["agendas"])
                    for cargo, info in agendas_por_cargo.items()
                },
            )
            response_processo = (
                self.processo_service.buscar_processo_convocacao(processo_uuid)
            )
            processo_data = response_processo.json()
            response_reclassificados = (
                self.candidatos_service.buscar_reclassificados_por_concurso(
                    concurso_uuid=processo_data.get("concurso_uuid"),
                    processo_uuid=processo_uuid,
                )
            )
            reclassificados_data = response_reclassificados.json()
            cargos_com_sessoes = []
            classificacao_max = 0
            classificacao_min = 0
            classificacao_max_sem_pcd = 0
            for cargo_info in agendas_por_cargo.values():
                cargo_nome = cargo_info["cargo_nome"]
                cargo_codigo = cargo_info["cargo_codigo"]
                agendas_cargo = cargo_info["agendas"]
                numero_sessoes = len(agendas_cargo)
                logger.info(
                    "Processando cargo: %s (%d sessões/agendas)",
                    cargo_nome,
                    numero_sessoes,
                )
                sessoes_cargo = []  # type: ignore[var-annotated]
                for agenda in agendas_cargo:
                    response_candidatos = (
                        self.candidatos_service.buscar_por_uuids(
                            uuids=agenda.get("candidatos_uuids"),
                            order_by=ordering,
                        )
                    )
                    dados_candidatos = response_candidatos.json()
                    candidatos_result = dados_candidatos.get("results", [])
                    _classificacoes = [
                        c.get("classificacao")
                        for c in candidatos_result
                        if c.get("classificacao") is not None
                    ]
                    classificacao_max_default = (
                        max(_classificacoes) if _classificacoes else 0
                    )
                    if any(
                        c.get("classificacao_pcd") is not None
                        for c in candidatos_result
                    ):
                        classificacao_max = classificacao_max_default
                        classificacao_max_sem_pcd = candidatos_result[-1].get(
                            "classificacao"
                        )
                    else:
                        classificacao_min = (
                            classificacao_max_sem_pcd or classificacao_max
                        )
                        classificacao_max = classificacao_max_default
                        classificacao_max_sem_pcd = 0
                    response_eliminados = (
                        self.candidatos_service.buscar_eliminados_por_concurso(
                            concurso_uuid=processo_data.get("concurso_uuid"),
                            processo_uuid=processo_uuid,
                            classificacao_max=classificacao_max,
                            classificacao_min=classificacao_min,
                        )
                    )
                    classificacao_min = classificacao_max
                    eliminados_data = response_eliminados.json()
                    candidatos_sep_cargo = self._separar_por_tipo(
                        candidatos_result
                    )
                    lacunas_geral = []
                    lacunas_nna = []
                    lacunas_pcd = []
                    if candidatos_sep_cargo["geral"]:
                        classificacoes_geral = self._extrair_classificacoes(
                            candidatos_sep_cargo["geral"], "classificacao"
                        )
                        lacunas_geral = self._identificar_lacunas(
                            classificacoes_geral
                        )
                    if candidatos_sep_cargo["nna"]:
                        classificacoes_nna = self._extrair_classificacoes(
                            candidatos_sep_cargo["nna"], "classificacao_nna"
                        )
                        lacunas_nna = self._identificar_lacunas(
                            classificacoes_nna
                        )
                    if candidatos_sep_cargo["pcd"]:
                        classificacoes_pcd = self._extrair_classificacoes(
                            candidatos_sep_cargo["pcd"], "classificacao_pcd"
                        )
                        lacunas_pcd = self._identificar_lacunas(
                            classificacoes_pcd
                        )
                    faltantes_todos = []
                    if lacunas_geral or lacunas_nna or lacunas_pcd:
                        if resultado.get("concurso_uuid") is None:
                            logger.info(
                                "Buscando detalhes do processo para processo_uuid=%s",  # noqa: E501
                                processo_uuid,
                            )
                            concurso_uuid = processo_data.get("concurso_uuid")
                            resultado["concurso_uuid"] = concurso_uuid
                            if concurso_uuid:
                                logger.info(
                                    "Buscando todos os processos do concurso %s",  # noqa: E501
                                    concurso_uuid,
                                )
                                (
                                    processo_uuid_principal,
                                    outros_processos_uuid,
                                ) = self.processo_service.separar_processos_por_principal(  # noqa: E501
                                    processo_data=processo_data
                                )
                                resultado["todos_processos_uuid"] = [
                                    processo_uuid_principal
                                ] + outros_processos_uuid  # type: ignore[assignment]
                                resultado["outros_processos_uuid"] = (
                                    outros_processos_uuid  # type: ignore[assignment]
                                )
                        if outros_processos_uuid:
                            candidatos_faltantes = self._buscar_candidatos_faltantes(  # noqa: E501
                                outros_processos_uuid=outros_processos_uuid,
                                lacunas_geral=lacunas_geral,
                                lacunas_nna=lacunas_nna,
                                lacunas_pcd=lacunas_pcd,
                                codigo_cargo=cargo_codigo,
                                ordering=ordering,
                            )
                            if candidatos_faltantes["geral"]:
                                candidatos_faltantes["geral"].sort(
                                    key=lambda x: x.get("classificacao")
                                    or float("inf")
                                )
                                faltantes_todos.extend(
                                    candidatos_faltantes["geral"]
                                )
                            if candidatos_faltantes["nna"]:
                                candidatos_faltantes["nna"].sort(
                                    key=lambda x: x.get("classificacao_nna")
                                    or float("inf")
                                )
                                faltantes_todos.extend(
                                    candidatos_faltantes["nna"]
                                )
                            if candidatos_faltantes["pcd"]:
                                candidatos_faltantes["pcd"].sort(
                                    key=lambda x: x.get("classificacao_pcd")
                                    or float("inf")
                                )
                                faltantes_todos.extend(
                                    candidatos_faltantes["pcd"]
                                )

                    def key_ranking_escolha(item: Any) -> Any:
                        """Executa key ranking escolha.

                        Args:
                            item: Parâmetro item.

                        Returns:
                            Resultado da operação.

                        Raises:
                            Nenhuma exceção específica documentada.
                        """
                        val = item.get("ranking_escolha")
                        return val if val is not None else float("inf")

                    def key_classificacao(item: Any) -> Any:
                        """Executa key classificacao.

                        Args:
                            item: Parâmetro item.

                        Returns:
                            Resultado da operação.

                        Raises:
                            Nenhuma exceção específica documentada.
                        """
                        val = item.get("classificacao")
                        return val if val is not None else float("inf")

                    candidatos_base_ordenados = sorted(
                        candidatos_result, key=key_ranking_escolha
                    )
                    if faltantes_todos:

                        def indices_lacunas_classificacao(
                            classificacoes_ordenadas: Any,
                        ) -> Any:
                            """Retorna mapa {valor_faltante: indice_insercao}.

                            Args:
                                classificacoes_ordenadas: Fixture do teste.

                            Returns:
                                Resultado da operação.

                            Raises:
                                Nenhuma exceção específica documentada.
                            """
                            gaps = {}  # type: ignore[var-annotated]
                            cont = 0
                            if not classificacoes_ordenadas:
                                return gaps
                            for i in range(len(classificacoes_ordenadas) - 1):
                                a = classificacoes_ordenadas[i]
                                b = classificacoes_ordenadas[i + 1]
                                if a is None or b is None:
                                    continue
                                if (
                                    isinstance(a, int)
                                    and isinstance(b, int)
                                    and (b - a > 1)
                                ):
                                    for offset, missing in enumerate(
                                        range(a + 1, b), start=1
                                    ):
                                        gaps[missing] = i + offset + cont
                                    cont += 1
                            return gaps

                        def _classificacao_para_gap(item: Any) -> Any:
                            """Executa  classificacao para gap.

                            Args:
                                item: Parâmetro item.

                            Returns:
                                Resultado da operação.

                            Raises:
                                Nenhuma exceção específica documentada.
                            """
                            return (
                                9999999
                                if item.get("categoria_efetiva") != "GERAL"
                                else item.get("classificacao")
                            )

                        classifs_base = [
                            _classificacao_para_gap(c)
                            for c in candidatos_base_ordenados
                            if _classificacao_para_gap(c) is not None
                        ]
                        mapa_lacunas = indices_lacunas_classificacao(
                            classifs_base
                        )
                        for faltante in faltantes_todos:
                            cls_f = faltante.get("classificacao")
                            if cls_f in mapa_lacunas:
                                pos = mapa_lacunas[cls_f]
                                candidatos_base_ordenados.insert(pos, faltante)
                            else:
                                pos = 0
                                while (
                                    pos < len(candidatos_base_ordenados)
                                    and key_classificacao(
                                        candidatos_base_ordenados[pos]
                                    )
                                    <= cls_f
                                ):
                                    pos += 1
                                candidatos_base_ordenados.insert(pos, faltante)
                    reclass_pcd = (
                        (reclassificados_data or {}).get("pcd", [])
                        if reclassificados_data
                        else []
                    )
                    self._inserir_reclassificados_em_segmento(
                        lista_segmento=candidatos_base_ordenados,
                        reclassificados=reclass_pcd,
                        cargo_codigo=cargo_codigo,
                        classificacao_attr="classificacao_pcd",
                    )
                    reclass_nna = (
                        (reclassificados_data or {}).get("nna", [])
                        if reclassificados_data
                        else []
                    )
                    self._inserir_reclassificados_em_segmento(
                        lista_segmento=candidatos_base_ordenados,
                        reclassificados=reclass_nna,
                        cargo_codigo=cargo_codigo,
                        classificacao_attr="classificacao_nna",
                    )
                    self._inserir_eliminados_em_segmento(
                        lista_segmento=candidatos_base_ordenados,
                        eliminados=(eliminados_data or {}).get("pcd", [])
                        if eliminados_data
                        else [],
                        cargo_codigo=cargo_codigo,
                        classificacao_attr="classificacao_pcd",
                    )
                    self._inserir_eliminados_em_segmento(
                        lista_segmento=candidatos_base_ordenados,
                        eliminados=(eliminados_data or {}).get("nna", [])
                        if eliminados_data
                        else [],
                        cargo_codigo=cargo_codigo,
                        classificacao_attr="classificacao_nna",
                    )
                    self._inserir_eliminados_em_segmento(
                        lista_segmento=candidatos_base_ordenados,
                        eliminados=(eliminados_data or {}).get("geral", [])
                        if eliminados_data
                        else [],
                        cargo_codigo=cargo_codigo,
                        classificacao_attr="classificacao",
                    )
                    numero_sessao = len(sessoes_cargo) + 1
                    agenda_sessao = (
                        agendas_cargo[numero_sessao - 1]
                        if numero_sessao - 1 < len(agendas_cargo)
                        else {}
                    )
                    sessoes_cargo.append(
                        {
                            "numero_sessao": numero_sessao,
                            "hora_convocacao_inicio": agenda_sessao.get(
                                "hora_convocacao_inicio", ""
                            ),
                            "hora_convocacao_fim": agenda_sessao.get(
                                "hora_convocacao_fim", ""
                            ),
                            "candidatos": candidatos_base_ordenados,
                        }
                    )
                cargos_com_sessoes.append(
                    {
                        "cargo_nome": cargo_nome,
                        "cargo_codigo": cargo_codigo,
                        "numero_sessoes": numero_sessoes,
                        "sessoes": sessoes_cargo,
                    }
                )
            for cargo_info in cargos_com_sessoes:
                ordem_escolha_contador = 0
                for sessao in cargo_info["sessoes"]:
                    candidatos_sessao = sessao.get("candidatos", [])
                    for candidato in candidatos_sessao:
                        if not candidato.get("status_especial"):
                            ordem_escolha_contador += 1
                            candidato["ordem_escolha"] = ordem_escolha_contador
                        else:
                            candidato["ordem_escolha"] = None
            resultado_estruturado = {
                "processo_uuid": resultado.get("processo_uuid"),
                "concurso_uuid": resultado.get("concurso_uuid"),
                "todos_processos_uuid": resultado.get("todos_processos_uuid"),
                "outros_processos_uuid": resultado.get(
                    "outros_processos_uuid"
                ),
                "total_cargos": len(cargos_com_sessoes),
                "cargos": [],
            }  # type: ignore[var-annotated]
            for cargo_info in cargos_com_sessoes:
                cargo_estruturado = {
                    "cargo_nome": cargo_info["cargo_nome"],
                    "cargo_codigo": cargo_info.get("cargo_codigo"),
                    "numero_sessoes": cargo_info["numero_sessoes"],
                    "sessoes": [],
                }
                for sessao in cargo_info["sessoes"]:
                    hora_inicio = sessao.get("hora_convocacao_inicio", "")
                    hora_fim = sessao.get("hora_convocacao_fim", "")
                    candidatos_sessao = sessao.get("candidatos", [])
                    if hora_inicio and hora_fim:
                        horario_formatado = f"{hora_inicio} às {hora_fim}"
                    else:
                        horario_formatado = "Não informado"
                    sessao_estruturada = {
                        "numero_sessao": sessao["numero_sessao"],
                        "hora_convocacao_inicio": hora_inicio,
                        "hora_convocacao_fim": hora_fim,
                        "horario_formatado": horario_formatado,
                        "total_candidatos": len(candidatos_sessao),
                        "candidatos": candidatos_sessao,
                    }
                    cargo_estruturado["sessoes"].append(sessao_estruturada)
                resultado_estruturado["cargos"].append(cargo_estruturado)  # type: ignore[union-attr]
            return resultado_estruturado
        except RequestException as exc:
            logger.error(
                "Erro ao processar lauda de convocação (processo_uuid=%s): %s",
                processo_uuid,
                exc,
            )
            raise
        except Exception as exc:
            logger.error(
                "Erro inesperado ao processar lauda de convocação (processo_uuid=%s): %s",  # noqa: E501
                processo_uuid,
                exc,
            )
            raise
