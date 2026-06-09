"""Módulo tests/services/relatorios/test_low_coverage_modules_extra."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock, patch

import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from relatorios.models import ConfiguracaoRelatorio, Parametrizacao
from relatorios.services.relatorios.lauda_vagas import LaudaVagas
from relatorios.services.relatorios.nao_escolhas import SumulaNaoEscolhas
from relatorios.services.relatorios.reconvocacao import SumulaReconvocacao
from relatorios.services.relatorios.relacao_vagas import RelacaoVagas

pytestmark = pytest.mark.django_db


class _Resp:
    """Define _Resp."""

    def __init__(self, payload: Any) -> None:
        """Executa   init  ."""
        self._payload = payload

    def json(self) -> Any:
        """Executa json."""
        return self._payload


def _req() -> Any:
    """Executa  req."""
    return RequestFactory().get("/api/v1/relatorios/")


@pytest.fixture
def parametrizacao() -> Any:
    """Executa parametrizacao."""
    return Parametrizacao.objects.get_or_create(cabecalho="CAB PADRAO")[0]


@pytest.fixture
def cfg_nao_escolhas() -> Any:
    """Executa cfg nao escolhas."""
    return ConfiguracaoRelatorio.objects.get_or_create(
        tipo="SUMULA_NAO_ESCOLHAS"
    )[0]


@pytest.fixture
def cfg_reconvocacao() -> Any:
    """Executa cfg reconvocacao."""
    return ConfiguracaoRelatorio.objects.get_or_create(
        tipo="SUMULA_RECONVOCACAO"
    )[0]


@pytest.fixture
def cfg_relacao_vagas() -> Any:
    """Executa cfg relacao vagas."""
    return ConfiguracaoRelatorio.objects.get_or_create(tipo="RELACAO_VAGAS")[0]


@pytest.fixture
def cfg_lauda_vagas() -> Any:
    """Executa cfg lauda vagas."""
    return ConfiguracaoRelatorio.objects.get_or_create(tipo="LAUDA_VAGAS")[0]


def _candidato_payload() -> Any:
    """Executa  candidato payload."""
    return {
        "results": [
            {
                "uuid": "cand-1",
                "codigo_cargo": "101",
                "descricao_cargo": "",
                "classificacao": 1,
                "classificacao_pcd": None,
                "classificacao_nna": 3,
                "candidato": {"nome": "Maria", "cpf": "111"},
            }
        ]
    }


def _cargos_payload() -> Any:
    """Executa  cargos payload."""
    return [{"cargo_codigo": "101", "cargo_nome": "Professor"}]


def _escolhas_payload(situacao: Any) -> Any:
    """Executa  escolhas payload."""
    return [{"candidato_uuid": "cand-1", "situacao": situacao}]


def _vagas_payload() -> Any:
    """Executa  vagas payload."""
    return {
        "vagas": [
            {
                "cargo_codigo": "101",
                "cargo_descricao": "Professor",
                "vagas_definitivas": 2,
                "vagas_precarias": 1,
                "vagas_definitivas_restantes": 1,
                "vagas_precarias_restantes": 1,
                "vagas_definitivas_utilizadas": 2,
                "vagas_precarias_utilizadas": 1,
                "escola": {
                    "tipo_ue": "EMEF",
                    "nome_oficial": "Escola A",
                    "codigo_eol": "999",
                    "dre": {"codigo": "D1", "nome": "DRE 1"},
                },
            }
        ]
    }


def test_sumula_nao_escolhas_gerar_html_and_json(
    cfg_nao_escolhas: Any, parametrizacao: Any
) -> None:
    """Verifica sumula nao escolhas gerar html and json."""
    svc = SumulaNaoEscolhas(
        configuracao=cfg_nao_escolhas, parametrizacao=parametrizacao
    )
    svc.processos_service = Mock()
    svc.candidatos_service = Mock()
    svc.escolhas_service = Mock()
    svc.processos_service.buscar_cargos_por_processo.return_value = _Resp(
        _cargos_payload()
    )
    svc.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = _Resp(  # noqa: E501
        _candidato_payload()
    )
    svc.escolhas_service.buscar_escolhas_por_candidatos.return_value = (
        _escolhas_payload("nao-escolha")
    )
    with patch(
        "relatorios.services.relatorios.nao_escolhas.render",
        return_value=HttpResponse("ok"),
    ):
        resp, dados = svc.gerar("proc-1", _req(), formato="html")
        assert resp.status_code == 200
        assert dados and dados[0]["codigo"] == "101"
    with patch.object(svc, "render_to_pdf", return_value=HttpResponse("pdf")):
        resp_pdf, _ = svc.gerar("proc-1", _req(), formato="pdf")
        assert resp_pdf.status_code == 200


def test_sumula_nao_escolhas_gerar_docx_and_xls(
    cfg_nao_escolhas: Any, parametrizacao: Any
) -> None:
    """Verifica sumula nao escolhas gerar docx and xls."""
    svc = SumulaNaoEscolhas(
        configuracao=cfg_nao_escolhas, parametrizacao=parametrizacao
    )
    svc.processos_service = Mock()
    svc.candidatos_service = Mock()
    svc.escolhas_service = Mock()
    svc.processos_service.buscar_cargos_por_processo.return_value = _Resp(
        _cargos_payload()
    )
    svc.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = _Resp(  # noqa: E501
        _candidato_payload()
    )
    svc.escolhas_service.buscar_escolhas_por_candidatos.return_value = (
        _escolhas_payload("nao-escolha")
    )
    with patch.object(
        svc, "render_to_docx", return_value=HttpResponse("docx")
    ):
        r_docx, _ = svc.gerar("proc-1", _req(), formato="docx")
        assert r_docx.status_code == 200
    with patch.object(svc, "render_to_xls", return_value=HttpResponse("xls")):
        r_xls, _ = svc.gerar("proc-1", _req(), formato="xls")
        assert r_xls.status_code == 200


def test_sumula_reconvocacao_gerar_paths(
    cfg_reconvocacao: Any, parametrizacao: Any
) -> None:
    """Verifica sumula reconvocacao gerar paths."""
    svc = SumulaReconvocacao(
        configuracao=cfg_reconvocacao, parametrizacao=parametrizacao
    )
    svc.processos_service = Mock()
    svc.candidatos_service = Mock()
    svc.escolhas_service = Mock()
    svc.processos_service.buscar_cargos_por_processo.return_value = _Resp(
        _cargos_payload()
    )
    svc.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = _Resp(  # noqa: E501
        _candidato_payload()
    )
    svc.escolhas_service.buscar_escolhas_por_candidatos.return_value = (
        _escolhas_payload("reconvocacao")
    )
    with patch(
        "relatorios.services.relatorios.reconvocacao.render",
        return_value=HttpResponse("ok"),
    ):
        resp, dados = svc.gerar("proc-2", _req(), formato="html")
        assert resp.status_code == 200
        assert dados and dados[0]["descricao"]
    with patch.object(svc, "render_to_pdf", return_value=HttpResponse("pdf")):
        assert svc.gerar("proc-2", _req(), formato="pdf")[0].status_code == 200
    with patch.object(
        svc, "render_to_docx", return_value=HttpResponse("docx")
    ):
        assert (
            svc.gerar("proc-2", _req(), formato="docx")[0].status_code == 200
        )
    with patch.object(svc, "render_to_xls", return_value=HttpResponse("xls")):
        assert svc.gerar("proc-2", _req(), formato="xls")[0].status_code == 200


def test_relacao_vagas_and_lauda_vagas_grouping_and_routes(
    cfg_relacao_vagas: Any, cfg_lauda_vagas: Any, parametrizacao: Any
) -> None:
    """Verifica relacao vagas and lauda vagas grouping and routes."""
    relacao = RelacaoVagas(
        configuracao=cfg_relacao_vagas, parametrizacao=parametrizacao
    )
    lauda = LaudaVagas(
        configuracao=cfg_lauda_vagas, parametrizacao=parametrizacao
    )
    relacao.escolhas_service = Mock()
    lauda.escolhas_service = Mock()
    relacao.escolhas_service.buscar_vagas_escolas.return_value = _Resp(
        _vagas_payload()
    )
    lauda.escolhas_service.buscar_vagas_escolas.return_value = _Resp(
        _vagas_payload()
    )
    with patch(
        "relatorios.services.relatorios.relacao_vagas.render",
        return_value=HttpResponse("ok"),
    ):
        resp_r, dados_r = relacao.gerar("proc-3", _req(), formato="html")
        assert resp_r.status_code == 200
        assert dados_r and dados_r[0]["codigo"] == "101"
    with patch.object(
        relacao, "render_to_xls", return_value=HttpResponse("xls")
    ):
        assert (
            relacao.gerar("proc-3", _req(), formato="xls")[0].status_code
            == 200
        )
    with patch.object(
        relacao, "render_to_docx", return_value=HttpResponse("docx")
    ):
        assert (
            relacao.gerar("proc-3", _req(), formato="docx")[0].status_code
            == 200
        )
    with patch.object(
        relacao, "render_to_pdf", return_value=HttpResponse("pdf")
    ):
        assert (
            relacao.gerar("proc-3", _req(), formato="pdf")[0].status_code
            == 200
        )
    with patch(
        "relatorios.services.relatorios.lauda_vagas.render",
        return_value=HttpResponse("ok"),
    ):
        resp_l, dados_l = lauda.gerar("proc-4", _req(), formato="html")
        assert resp_l.status_code == 200
        assert dados_l and dados_l[0]["dres"]
    with patch.object(
        lauda, "render_to_xls", return_value=HttpResponse("xls")
    ):
        assert (
            lauda.gerar("proc-4", _req(), formato="xls")[0].status_code == 200
        )
    with patch.object(
        lauda, "render_to_docx", return_value=HttpResponse("docx")
    ):
        assert (
            lauda.gerar("proc-4", _req(), formato="docx")[0].status_code == 200
        )
    with patch.object(
        lauda, "render_to_pdf", return_value=HttpResponse("pdf")
    ):
        assert (
            lauda.gerar("proc-4", _req(), formato="pdf")[0].status_code == 200
        )


def test_modules_raise_when_upstream_fails(
    cfg_nao_escolhas: Any,
    cfg_reconvocacao: Any,
    cfg_relacao_vagas: Any,
    cfg_lauda_vagas: Any,
    parametrizacao: Any,
) -> None:
    """Verifica modules raise when upstream fails."""
    nao = SumulaNaoEscolhas(
        configuracao=cfg_nao_escolhas, parametrizacao=parametrizacao
    )
    nao.processos_service = Mock()
    nao.candidatos_service = Mock()
    nao.escolhas_service = Mock()
    nao.candidatos_service.buscar_concurso_candidatos_por_processo.side_effect = RuntimeError(  # noqa: E501
        "erro candidatos"
    )
    with pytest.raises(RuntimeError):
        nao.gerar("proc", _req(), formato="html")
    reco = SumulaReconvocacao(
        configuracao=cfg_reconvocacao, parametrizacao=parametrizacao
    )
    reco.processos_service = Mock()
    reco.candidatos_service = Mock()
    reco.escolhas_service = Mock()
    reco.processos_service.buscar_cargos_por_processo.side_effect = (
        RuntimeError("erro cargos")
    )
    reco.candidatos_service.buscar_concurso_candidatos_por_processo.return_value = _Resp(  # noqa: E501
        {"results": []}
    )
    reco.escolhas_service.buscar_escolhas_por_candidatos.return_value = []
    with patch(
        "relatorios.services.relatorios.reconvocacao.render",
        return_value=HttpResponse("ok"),
    ):
        reco.gerar("proc", _req(), formato="html")
    relacao = RelacaoVagas(
        configuracao=cfg_relacao_vagas, parametrizacao=parametrizacao
    )
    relacao.escolhas_service = Mock()
    relacao.escolhas_service.buscar_vagas_escolas.side_effect = RuntimeError(
        "erro vagas"
    )
    with pytest.raises(RuntimeError):
        relacao.gerar("proc", _req(), formato="html")
    lauda = LaudaVagas(
        configuracao=cfg_lauda_vagas, parametrizacao=parametrizacao
    )
    lauda.escolhas_service = Mock()
    lauda.escolhas_service.buscar_vagas_escolas.side_effect = RuntimeError(
        "erro vagas"
    )
    with pytest.raises(RuntimeError):
        lauda.gerar("proc", _req(), formato="html")
