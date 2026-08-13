"""Testes do utilitário de histórico de classificação."""

from __future__ import annotations

from relatorios.services.historico_classificacao import (
    aplicar_historico_classificacao,
)


def test_aplicar_historico_classificacao_restaura_quando_foi_convocado() -> None:
    """Restaura classificações anteriores quando foi_convocado=True."""
    candidatos = [
        {
            "uuid": "c1",
            "classificacao": 4,
            "classificacao_nna": 5,
            "classificacao_pcd": 6,
            "historico_classificacao": [
                {
                    "classificacao_anterior": 2,
                    "classificacao_nova": 4,
                    "classificacao_nna_anterior": 1,
                    "classificacao_nna_nova": 5,
                    "classificacao_pcd_anterior": 3,
                    "classificacao_pcd_nova": 6,
                    "foi_convocado": True,
                }
            ],
        }
    ]
    resultado = aplicar_historico_classificacao(candidatos)
    assert resultado[0]["classificacao"] == 2
    assert resultado[0]["classificacao_nna"] == 1
    assert resultado[0]["classificacao_pcd"] == 3


def test_aplicar_historico_classificacao_ignora_sem_foi_convocado() -> None:
    """Não altera classificações quando nenhum histórico tem foi_convocado."""
    candidatos = [
        {
            "uuid": "c1",
            "classificacao": 4,
            "classificacao_nna": None,
            "historico_classificacao": [
                {
                    "classificacao_anterior": 2,
                    "classificacao_nova": 4,
                    "classificacao_nna_anterior": None,
                    "foi_convocado": False,
                }
            ],
        }
    ]
    resultado = aplicar_historico_classificacao(candidatos)
    assert resultado[0]["classificacao"] == 4
    assert resultado[0]["classificacao_nna"] is None


def test_aplicar_historico_classificacao_sem_historico_nao_altera() -> None:
    """Mantém candidato intacto quando não há histórico preenchido."""
    candidatos = [
        {"uuid": "c1", "classificacao": 4, "historico_classificacao": []},
        {"uuid": "c2", "classificacao": 7},
    ]
    resultado = aplicar_historico_classificacao(candidatos)
    assert resultado[0]["classificacao"] == 4
    assert resultado[1]["classificacao"] == 7


def test_aplicar_historico_classificacao_so_campos_com_anterior() -> None:
    """Substitui apenas campos cujo *_anterior veio preenchido."""
    candidatos = [
        {
            "uuid": "c1",
            "classificacao": 4,
            "classificacao_nna": 9,
            "classificacao_pcd": 8,
            "historico_classificacao": [
                {
                    "classificacao_anterior": 2,
                    "classificacao_nna_anterior": None,
                    "classificacao_pcd_anterior": None,
                    "foi_convocado": True,
                }
            ],
        }
    ]
    resultado = aplicar_historico_classificacao(candidatos)
    assert resultado[0]["classificacao"] == 2
    assert resultado[0]["classificacao_nna"] == 9
    assert resultado[0]["classificacao_pcd"] == 8
