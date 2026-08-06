"""Utilitário para restaurar classificações a partir do histórico."""

from __future__ import annotations

from typing import Any


def aplicar_historico_classificacao(
    candidatos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Restaura classificações a partir do histórico de deslocamento.

    Para cada candidato com ``historico_classificacao`` preenchido, busca
    o registro com ``foi_convocado=True`` e, quando houver valor em
    ``classificacao_*_anterior``, substitui a classificação atual do item
    (geral, NNA ou PCD).

    Args:
        candidatos: Lista de candidatos retornada pela API.

    Returns:
        A mesma lista, com classificações ajustadas quando aplicável.
    """
    for candidato in candidatos:
        historicos = candidato.get("historico_classificacao") or []
        if not historicos:
            continue
        historico_convocado = next(
            (
                item
                for item in historicos
                if item.get("foi_convocado") is True
            ),
            None,
        )
        if historico_convocado is None:
            continue
        if historico_convocado.get("classificacao_anterior") is not None:
            candidato["classificacao"] = historico_convocado[
                "classificacao_anterior"
            ]
        if historico_convocado.get("classificacao_nna_anterior") is not None:
            candidato["classificacao_nna"] = historico_convocado[
                "classificacao_nna_anterior"
            ]
        if historico_convocado.get("classificacao_pcd_anterior") is not None:
            candidato["classificacao_pcd"] = historico_convocado[
                "classificacao_pcd_anterior"
            ]
    return candidatos
