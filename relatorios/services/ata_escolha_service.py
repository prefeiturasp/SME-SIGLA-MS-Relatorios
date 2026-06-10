"""Serviço para geração de Ata de Escolha.

Baseado no padrão da Lauda de Convocação, mas com informações da escola
escolhida.
"""

from __future__ import annotations

import logging
from typing import Any

from requests import RequestException

from .candidatos_api_service import CandidatosService


class CargoObrigatorioError(Exception):
    """Exceção levantada quando o processo tem mais de um cargo e o cargo."""

    def __init__(
        self,
        cargos: list[dict],
        message: str = "Selecione um cargo para emitir a Ata de Escolha.",
    ) -> None:
        """Inicializa a instância com os parâmetros informados.

        Args:
            self: Instância do objeto.
            cargos: Cargos utilizado na operação.
            message: Message utilizado na operação.
        """
        self.cargos = cargos
        self.message = message
        super().__init__(message)


from .agendas_api_service import AgendasService
from .escolhas_api_service import EscolhasService
from .processo_convocacao_api_service import ProcessoConvocacaoService

logger = logging.getLogger(__name__)


class AtaEscolhaService:
    """Serviço para geração de Ata de Escolha."""

    def __init__(
        self,
        candidatos_base_url: str = "https://example.com",
        processo_base_url: str = "https://example.com",
        agendas_base_url: str = "https://example.com",
        escolhas_base_url: str = "https://example.com",
        timeout_seconds: int = 30,
    ) -> None:
        """Inicializa a instância com os parâmetros informados.

        Args:
            self: Instância do objeto.
            candidatos_base_url: Candidatos base url utilizado na operação.
            processo_base_url: Processo base url utilizado na operação.
            agendas_base_url: Agendas base url utilizado na operação.
            escolhas_base_url: Escolhas base url utilizado na operação.
            timeout_seconds: Tempo máximo de espera pela resposta, em segundos.
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
            classificacoes: Classificacoes utilizado na operação.

        Returns:
            Lista com os registros obtidos.
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
        """Separa candidatos por categoria_efetiva (GERAL, NNA e PCD).

        Args:
            self: Instância do objeto.
            candidatos: Candidatos utilizado na operação.

        Returns:
            Dicionário com os dados retornados pela operação.
        """
        separados = {"pcd": [], "geral": [], "nna": []}  # type: ignore[var-annotated]
        for candidato in candidatos:
            categoria_efetiva = candidato.get("categoria_efetiva")
            if categoria_efetiva == "PCD":
                separados["pcd"].append(candidato)
            elif categoria_efetiva == "GERAL":
                separados["geral"].append(candidato)
            elif categoria_efetiva == "NNA":
                separados["nna"].append(candidato)
        return separados

    def _extrair_classificacoes(
        self, candidatos: list[dict], campo: str
    ) -> list[int]:
        """Extrai classificações de uma lista de candidatos.

        Args:
            self: Instância do objeto.
            candidatos: Candidatos utilizado na operação.
            campo: Campo utilizado na operação.

        Returns:
            Lista com os registros obtidos.
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
        """Busca candidatos faltantes em outros processos do concurso.

        Args:
            self: Instância do objeto.
            outros_processos_uuid: UUID de outros processos.
            lacunas_geral: Lacunas geral utilizado na operação.
            lacunas_nna: Lacunas nna utilizado na operação.
            lacunas_pcd: Lacunas pcd utilizado na operação.
            codigo_cargo: Codigo cargo utilizado na operação.
            ordering: Ordering utilizado na operação.

        Returns:
            Dicionário com os dados retornados pela operação.
        """
        candidatos_faltantes = {"geral": [], "nna": [], "pcd": []}  # type: ignore[var-annotated]
        if not outros_processos_uuid:
            return candidatos_faltantes
        try:
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
                for candidato in candidatos_faltantes["pcd"]:
                    candidato["status_especial"] = (
                        "CANDIDATOS JÁ CLASSIFICADO."
                    )
                logger.info(
                    "Encontrados %d candidatos PCD faltantes",
                    len(candidatos_faltantes["pcd"]),
                )
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
                for candidato in candidatos_faltantes["geral"]:
                    candidato["status_especial"] = (
                        "JÁ CONVOCADO - LEI 13.398/02"
                        if candidato.get("classificacao_nna") is not None
                        else "JÁ CONVOCADO - LEI 15.939/13"
                        if candidato.get("classificacao_pcd") is not None
                        else ""
                    )
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
                for candidato in candidatos_faltantes["nna"]:
                    candidato["status_especial"] = (
                        "CANDIDATOS JÁ CLASSIFICADO."
                    )
                logger.info(
                    "Encontrados %d candidatos NNA faltantes",
                    len(candidatos_faltantes["nna"]),
                )
        except RequestException as exc:
            logger.warning(
                "Erro ao buscar candidatos faltantes nos outros processos: %s",
                exc,
            )
        return candidatos_faltantes

    def _buscar_escolhas_por_candidatos(
        self, candidato_uuids: list[str]
    ) -> dict[str, dict]:
        """Busca escolhas por lista de candidato_uuids e retorna um mapa.

        Args:
            self: Instância do objeto.
            candidato_uuids: Candidato uuids utilizado na operação.

        Returns:
            Dicionário com os dados retornados pela operação.
        """
        escolhas_map = {}  # type: ignore[var-annotated]
        if not candidato_uuids:
            return escolhas_map
        try:
            escolhas_data = (
                self.escolhas_service.buscar_escolhas_por_candidatos(
                    candidato_uuids=candidato_uuids, situacao=None
                )
            )  # type: ignore[arg-type]
            for escolha in escolhas_data:
                candidato_uuid = escolha.get("candidato_uuid")
                if candidato_uuid:
                    escolhas_map[str(candidato_uuid)] = escolha
            logger.info(
                "Encontradas %d escolhas para %d candidatos",
                len(escolhas_map),
                len(candidato_uuids),
            )
        except RequestException as exc:
            logger.warning("Erro ao buscar escolhas: %s", exc)
        return escolhas_map

    def _extrair_dados_escola_escolhida(self, escolha: dict) -> dict:
        """Extrai dados da escola escolhida de uma escolha.

        Args:
            self: Instância do objeto.
            escolha: Escolha utilizado na operação.

        Returns:
            Dicionário com os dados retornados pela operação.
        """
        vaga_escola = escolha.get("vaga_escola", {})
        escola = (
            vaga_escola.get("escola", {})
            if isinstance(vaga_escola, dict)
            else {}
        )
        dre = escola.get("dre", {}) if isinstance(escola, dict) else {}
        codigo_eol = (
            escola.get("codigo_eol", "") if isinstance(escola, dict) else ""
        )
        dre_codigo = (
            dre.get("sigla", "") or dre.get("SIGLA", "")
            if isinstance(dre, dict)
            else ""
        )
        dre_nome = dre.get("nome", "") if isinstance(dre, dict) else ""
        tipo_unidade = (
            escola.get("tipo_ue", "")
            or escola.get("TIPO_UE", "")
            or escola.get("tipo_unidade", "")
            if isinstance(escola, dict)
            else ""
        )
        nome_escola = (
            escola.get("nome_oficial", "") if isinstance(escola, dict) else ""
        )
        tipo_vaga_raw = escolha.get("tipo_vaga", "")
        if tipo_vaga_raw == "precaria":
            tipo_vaga = "P"
        elif tipo_vaga_raw == "definitiva":
            tipo_vaga = "D"
        else:
            tipo_vaga = ""
        return {
            "codigo_eol": codigo_eol,
            "dre_codigo": dre_codigo,
            "dre_nome": dre_nome,
            "tipo_unidade": tipo_unidade,
            "nome_escola": nome_escola,
            "tipo_vaga": tipo_vaga,
        }

    def _contar_escolhas_por_situacao(
        self, escolhas: list[dict]
    ) -> dict[str, int]:
        """Conta quantas escolhas existem por situação.

        Args:
            self: Instância do objeto.
            escolhas: Escolhas utilizado na operação.

        Returns:
            Dicionário com os dados retornados pela operação.
        """
        contadores = {"escolha": 0, "nao_escolha": 0, "reconvocacao": 0}
        normalizar = {
            "escolha": "escolha",
            "nao-escolha": "nao_escolha",
            "nao_escolha": "nao_escolha",
            "reconvocacao": "reconvocacao",
        }
        for escolha in escolhas:
            situacao_raw = escolha.get("situacao")
            if not isinstance(situacao_raw, str):
                continue
            situacao = situacao_raw.strip().lower()
            chave = normalizar.get(situacao)
            if chave in contadores:
                contadores[chave] += 1
        contadores["nao-escolha"] = contadores["nao_escolha"]
        return contadores

    def _contar_escolhas_por_situacao_por_tipo(
        self,
        candidatos_sep_cargo: dict[str, list[dict]],
        escolhas_map: dict[str, dict],
    ) -> dict[str, dict[str, int]]:
        """Conta as escolhas por situação separadas por tipo de candidato.

        Args:
            self: Instância do objeto.
            candidatos_sep_cargo: Candidatos sep cargo utilizado na operação.
            escolhas_map: Escolhas map utilizado na operação.

        Returns:
            Dicionário com os dados retornados pela operação.
        """
        resultado: dict[str, dict[str, int]] = {}
        normalizar = {
            "escolha": "escolha",
            "nao-escolha": "nao_escolha",
            "nao_escolha": "nao_escolha",
            "reconvocacao": "reconvocacao",
        }
        for tipo in ("pcd", "geral", "nna"):
            candidatos_tipo = candidatos_sep_cargo.get(tipo) or []
            uuids_tipo = {
                str(c.get("uuid"))
                for c in candidatos_tipo
                if c.get("uuid") is not None
            }
            cont = {"escolha": 0, "nao_escolha": 0, "reconvocacao": 0}
            for cand_uuid in uuids_tipo:
                esc = escolhas_map.get(cand_uuid)
                if not esc:
                    continue
                situacao_raw = esc.get("situacao")
                if not isinstance(situacao_raw, str):
                    continue
                situacao = situacao_raw.strip().lower()
                chave = normalizar.get(situacao)
                if chave:
                    cont[chave] += 1
            cont["nao-escolha"] = cont["nao_escolha"]
            resultado[tipo] = cont
        return resultado

    def processar_ata_escolha(
        self,
        processo_uuid: str,
        cargo_codigo: str | None = None,
        ordering: str = "ranking_escolha",
    ) -> dict:
        """Processa ata escolha.

        Args:
            self: Instância do objeto.
            processo_uuid: UUID do processo de convocação.
            cargo_codigo: Cargo codigo utilizado na operação.
            ordering: Ordering utilizado na operação.

        Returns:
            Dicionário com os dados retornados pela operação.

        Raises:
            CargoObrigatorioError: Se ocorrer erro nesta operação.
            ValueError: Se os dados informados forem inválidos.
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
                cod = agenda.get("cargo_codigo")
                if cod and cod not in codigos_cargo:
                    codigos_cargo.append(cod)
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
                cod = agenda.get("cargo_codigo")
                if cod not in agendas_por_cargo:
                    agendas_por_cargo[cod] = {
                        "cargo_nome": cargo_nome,
                        "cargo_codigo": cod,
                        "agendas": [],
                    }
                agendas_por_cargo[cod]["agendas"].append(agenda)
                if not agendas_por_cargo[cod]["cargo_codigo"] and cod:
                    agendas_por_cargo[cod]["cargo_codigo"] = cod
            logger.info(
                "Agendas agrupadas por cargo: %s",
                {
                    c: len(info["agendas"])
                    for c, info in agendas_por_cargo.items()
                },
            )
            cargos_lista = [
                {"cargo_codigo": c, "cargo_nome": info["cargo_nome"]}
                for c, info in agendas_por_cargo.items()
            ]
            if len(agendas_por_cargo) > 1:
                if not cargo_codigo:
                    raise CargoObrigatorioError(cargos=cargos_lista)
                if cargo_codigo not in agendas_por_cargo:
                    raise ValueError(
                        f"Cargo '{cargo_codigo}' não encontrado no processo."
                    )
                agendas_por_cargo = {
                    cargo_codigo: agendas_por_cargo[cargo_codigo]
                }
            elif len(agendas_por_cargo) == 1 and cargo_codigo is None:
                unico = next(iter(agendas_por_cargo.keys()))
                agendas_por_cargo = {unico: agendas_por_cargo[unico]}
            cargos_com_sessoes = []
            response_processo = (
                self.processo_service.buscar_processo_convocacao(processo_uuid)
            )
            processo_data = response_processo.json()
            classificacoes_pcd, classificacoes_nna, classificacoes_geral = (
                [],
                [],
                [],
            )
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
                todos_candidatos_uuids = []
                for _agenda in agendas_cargo:
                    for _uuid in _agenda.get("candidatos_uuids", []):
                        if _uuid not in todos_candidatos_uuids:
                            todos_candidatos_uuids.append(_uuid)
                logger.info(
                    "Buscando candidatos por UUIDs (cargo=%s, total=%d)",
                    cargo_codigo,
                    len(todos_candidatos_uuids),
                )
                response_candidatos = self.candidatos_service.buscar_por_uuids(
                    uuids=todos_candidatos_uuids, order_by=ordering
                )
                dados_cargo = response_candidatos.json()
                if isinstance(dados_cargo, dict) and "results" in dados_cargo:
                    candidatos_cargo = dados_cargo["results"]
                elif isinstance(dados_cargo, list):
                    candidatos_cargo = dados_cargo
                else:
                    logger.warning(
                        "Resposta inesperada ao buscar candidatos por UUIDs para cargo %s",  # noqa: E501
                        cargo_codigo,
                    )
                    candidatos_cargo = []
                candidatos_sep_cargo = self._separar_por_tipo(candidatos_cargo)
                lacunas_geral = []
                lacunas_nna = []
                lacunas_pcd = []
                if candidatos_sep_cargo["pcd"]:
                    classificacoes_pcd = self._extrair_classificacoes(
                        candidatos_sep_cargo["pcd"], "classificacao_pcd"
                    )
                    lacunas_pcd = self._identificar_lacunas(classificacoes_pcd)
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
                    lacunas_nna = self._identificar_lacunas(classificacoes_nna)
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
                                "Buscando todos os processos do concurso %s",
                                concurso_uuid,
                            )
                            processo_uuid_principal, outros_processos_uuid = (
                                self.processo_service.separar_processos_por_principal(
                                    processo_data=processo_data
                                )
                            )
                            resultado["todos_processos_uuid"] = [
                                processo_uuid_principal
                            ] + outros_processos_uuid  # type: ignore[assignment]
                            resultado["outros_processos_uuid"] = (
                                outros_processos_uuid  # type: ignore[assignment]
                            )
                    if outros_processos_uuid:
                        candidatos_faltantes = (
                            self._buscar_candidatos_faltantes(
                                outros_processos_uuid=outros_processos_uuid,
                                lacunas_geral=lacunas_geral,
                                lacunas_nna=lacunas_nna,
                                lacunas_pcd=lacunas_pcd,
                                codigo_cargo=cargo_codigo,
                                ordering=ordering,
                            )
                        )
                        if candidatos_faltantes["pcd"]:
                            candidatos_faltantes["pcd"].sort(
                                key=lambda x: x.get("classificacao_pcd")
                                or float("inf")
                            )
                            faltantes_todos.extend(candidatos_faltantes["pcd"])
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
                            faltantes_todos.extend(candidatos_faltantes["nna"])

                def key_ranking_escolha(item: Any) -> Any:
                    """Key ranking escolha.

                    Args:
                        item: Item utilizado na operação.

                    Returns:
                        Valor calculado conforme a regra aplicada.
                    """
                    val = item.get("ranking_escolha")
                    return val if val is not None else float("inf")

                def key_categoria_efetiva(item: Any) -> Any:
                    """Key categoria efetiva.

                    Args:
                        item: Item utilizado na operação.

                    Returns:
                        Valor calculado conforme a regra aplicada.
                    """
                    categoria = item.get("categoria_efetiva", "")
                    if categoria == "PCD":
                        return 0
                    elif categoria == "GERAL":
                        return 1
                    elif categoria == "NNA":
                        return 2
                    return 3

                def key_classificacao(item: Any) -> Any:
                    """Key classificacao.

                    Args:
                        item: Item utilizado na operação.

                    Returns:
                        Valor calculado conforme a regra aplicada.
                    """
                    val = item.get("classificacao")
                    return val if val is not None else float("inf")

                candidatos_base_ordenados = sorted(
                    candidatos_cargo,
                    key=lambda x: (
                        key_categoria_efetiva(x),
                        key_ranking_escolha(x),
                    ),
                )
                if faltantes_todos:

                    def indices_lacunas_classificacao(
                        classificacoes_ordenadas: Any,
                    ) -> Any:
                        """Mapeia lacunas de classificação para inserção.

                        Args:
                            classificacoes_ordenadas: Classificações ordenadas.

                        Returns:
                            Valor calculado conforme a regra aplicada.
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
                        """Classificacao para gap.

                        Args:
                            item: Item utilizado na operação.

                        Returns:
                            Valor calculado conforme a regra aplicada.
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
                    mapa_lacunas = indices_lacunas_classificacao(classifs_base)
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
                candidato_uuids = [
                    c.get("uuid")
                    for c in candidatos_base_ordenados
                    if c.get("uuid")
                ]
                escolhas_map = self._buscar_escolhas_por_candidatos(
                    candidato_uuids
                )
                for candidato in candidatos_base_ordenados:
                    candidato_uuid = candidato.get("uuid")
                    escolha = (
                        escolhas_map.get(str(candidato_uuid))
                        if candidato_uuid
                        else None
                    )
                    candidato_obj = (
                        candidato.get("candidato", {})
                        if isinstance(candidato.get("candidato"), dict)
                        else {}
                    )
                    candidato["nome"] = (
                        candidato_obj.get("nome", "")
                        if isinstance(candidato_obj, dict)
                        else ""
                    )
                    candidato["rg"] = (
                        candidato_obj.get("rg", "")
                        if isinstance(candidato_obj, dict)
                        else ""
                    )
                    candidato["cpf"] = (
                        candidato_obj.get("cpf", "")
                        if isinstance(candidato_obj, dict)
                        else ""
                    )
                    candidato["rf"] = (
                        candidato_obj.get("registro_funcional", "")
                        if isinstance(candidato_obj, dict)
                        else ""
                    )
                    if escolha and escolha.get("situacao") == "escolha":
                        dados_escola = self._extrair_dados_escola_escolhida(
                            escolha
                        )
                        candidato["escolha"] = dados_escola
                        candidato["assinatura"] = "Escolha"
                        candidato["codigo_eol"] = dados_escola.get(
                            "codigo_eol", ""
                        )
                        candidato["dre_codigo"] = dados_escola.get(
                            "dre_codigo", ""
                        )
                        candidato["dre_nome"] = dados_escola.get(
                            "dre_nome", ""
                        )
                        candidato["tipo_unidade"] = dados_escola.get(
                            "tipo_unidade", ""
                        )
                        candidato["nome_escola_escolhida"] = dados_escola.get(
                            "nome_escola", ""
                        )
                        candidato["tipo_vaga"] = dados_escola.get(
                            "tipo_vaga", ""
                        )
                    else:
                        candidato["escolha"] = None
                        candidato["assinatura"] = "Não Escolha"
                        candidato["codigo_eol"] = ""
                        candidato["dre_codigo"] = ""
                        candidato["dre_nome"] = ""
                        candidato["tipo_unidade"] = ""
                        candidato["nome_escola_escolhida"] = ""
                        candidato["tipo_vaga"] = ""
                uuids_separadores_cargo = []
                acumulado = 0
                for i in range(len(agendas_cargo) - 1):
                    agenda = agendas_cargo[i]
                    candidatos_uuids = agenda.get("candidatos_uuids", [])
                    quantidade_candidatos = len(candidatos_uuids)
                    posicao = acumulado + quantidade_candidatos
                    if posicao < len(candidatos_cargo):
                        candidatos_cargo[posicao]
                        uuid_separador = candidatos_cargo[posicao].get("uuid")
                        if uuid_separador:
                            uuids_separadores_cargo.append(uuid_separador)
                            logger.info(
                                "Cargo %s - Agenda %d: quantidade=%d, posição=%d, UUID separador=%s",  # noqa: E501
                                cargo_nome,
                                i + 1,
                                quantidade_candidatos,
                                posicao,
                                uuid_separador,
                            )
                    acumulado += quantidade_candidatos
                sessoes_cargo = []
                indices_usados = set()  # type: ignore[var-annotated]
                if not uuids_separadores_cargo:
                    agenda_primeira = agendas_cargo[0] if agendas_cargo else {}
                    sessoes_cargo.append(
                        {
                            "numero_sessao": 1,
                            "hora_convocacao_inicio": agenda_primeira.get(
                                "hora_convocacao_inicio", ""
                            ),
                            "hora_convocacao_fim": agenda_primeira.get(
                                "hora_convocacao_fim", ""
                            ),
                            "candidatos": candidatos_base_ordenados,
                        }
                    )
                else:
                    for idx_uuid, uuid_separador in enumerate(
                        uuids_separadores_cargo
                    ):
                        posicao_encontrada = None
                        for idx_candidato, candidato in enumerate(
                            candidatos_base_ordenados
                        ):
                            if (
                                candidato.get("uuid") == uuid_separador
                                and idx_candidato not in indices_usados
                            ):
                                posicao_encontrada = idx_candidato
                                break
                        if posicao_encontrada is not None:
                            if idx_uuid == 0:
                                indice_inicial = 0
                            else:
                                indice_inicial = (
                                    max(indices_usados) + 1
                                    if indices_usados
                                    else 0
                                )
                            lista_segmento = candidatos_base_ordenados[
                                indice_inicial:posicao_encontrada
                            ]
                            if lista_segmento:
                                numero_sessao = len(sessoes_cargo) + 1
                                agenda_sessao = (
                                    agendas_cargo[numero_sessao - 1]
                                    if numero_sessao - 1 < len(agendas_cargo)
                                    else {}
                                )
                                sessoes_cargo.append(
                                    {
                                        "numero_sessao": numero_sessao,
                                        "hora_convocacao_inicio": agenda_sessao.get(  # noqa: E501
                                            "hora_convocacao_inicio", ""
                                        ),
                                        "hora_convocacao_fim": agenda_sessao.get(  # noqa: E501
                                            "hora_convocacao_fim", ""
                                        ),
                                        "candidatos": lista_segmento,
                                    }
                                )
                            for i in range(indice_inicial, posicao_encontrada):
                                indices_usados.add(i)
                            logger.info(
                                "Cargo %s - Sessão %d: %d candidatos (índice %d até %d) - Horário: %s às %s",  # noqa: E501
                                cargo_nome,
                                len(sessoes_cargo),
                                len(lista_segmento),
                                indice_inicial,
                                posicao_encontrada,
                                agenda_sessao.get(
                                    "hora_convocacao_inicio", "N/A"
                                ),
                                agenda_sessao.get(
                                    "hora_convocacao_fim", "N/A"
                                ),
                            )
                            if idx_uuid == len(uuids_separadores_cargo) - 1:
                                indice_proximo = posicao_encontrada
                                if indice_proximo < len(
                                    candidatos_base_ordenados
                                ):
                                    lista_final = candidatos_base_ordenados[
                                        indice_proximo:
                                    ]
                                    if lista_final:
                                        numero_sessao_final = (
                                            len(sessoes_cargo) + 1
                                        )
                                        agenda_final = (
                                            agendas_cargo[
                                                numero_sessao_final - 1
                                            ]
                                            if numero_sessao_final - 1
                                            < len(agendas_cargo)
                                            else {}
                                        )
                                        sessoes_cargo.append(
                                            {
                                                "numero_sessao": numero_sessao_final,  # noqa: E501
                                                "hora_convocacao_inicio": agenda_final.get(  # noqa: E501
                                                    "hora_convocacao_inicio",
                                                    "",
                                                ),
                                                "hora_convocacao_fim": agenda_final.get(  # noqa: E501
                                                    "hora_convocacao_fim", ""
                                                ),
                                                "candidatos": lista_final,
                                            }
                                        )
                                        logger.info(
                                            "Cargo %s - Sessão %d (final): %d candidatos - Horário: %s às %s",  # noqa: E501
                                            cargo_nome,
                                            len(sessoes_cargo),
                                            len(lista_final),
                                            agenda_final.get(
                                                "hora_convocacao_inicio", "N/A"
                                            ),
                                            agenda_final.get(
                                                "hora_convocacao_fim", "N/A"
                                            ),
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
                "processo_uuid": processo_data.get("uuid"),
                "processo_nome": processo_data.get("descricao"),
                "concurso_uuid": resultado.get("concurso_uuid"),
                "todos_processos_uuid": resultado.get("todos_processos_uuid"),
                "outros_processos_uuid": resultado.get(
                    "outros_processos_uuid"
                ),
                "total_cargos": len(cargos_com_sessoes),
                "candidatos_sep_cargo": candidatos_sep_cargo,
                "escolhas_totais": self._contar_escolhas_por_situacao(
                    list(escolhas_map.values())
                ),
                "escolhas_totais_por_tipo": self._contar_escolhas_por_situacao_por_tipo(  # noqa: E501
                    candidatos_sep_cargo=candidatos_sep_cargo,
                    escolhas_map=escolhas_map,
                ),
                "cargos": [],
                "intervalos_classificacoes": {
                    "pcd": {
                        "min": min(classificacoes_pcd)
                        if classificacoes_pcd
                        else 0,
                        "max": max(classificacoes_pcd)
                        if classificacoes_pcd
                        else 0,
                    },
                    "geral": {
                        "min": min(classificacoes_geral)
                        if classificacoes_geral
                        else 0,
                        "max": max(classificacoes_geral)
                        if classificacoes_geral
                        else 0,
                    },
                    "nna": {
                        "min": min(classificacoes_nna)
                        if classificacoes_nna
                        else 0,
                        "max": max(classificacoes_nna)
                        if classificacoes_nna
                        else 0,
                    },
                },
            }
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
                resultado_estruturado["cargos"].append(cargo_estruturado)
            return resultado_estruturado
        except RequestException as exc:
            logger.error(
                "Erro ao processar ata de escolha (processo_uuid=%s): %s",
                processo_uuid,
                exc,
            )
            raise
        except Exception as exc:
            logger.error(
                "Erro inesperado ao processar ata de escolha (processo_uuid=%s): %s",  # noqa: E501
                processo_uuid,
                exc,
            )
            raise
