"""Módulo views/__init__."""
from .parametrizacao import ParametrizacaoViewSet
from .personalizacao import PersonalizacaoViewSet
from .relatorios import RelatorioViewSet

__all__ = [
    "RelatorioViewSet",
    "ParametrizacaoViewSet",
    "PersonalizacaoViewSet",
]
