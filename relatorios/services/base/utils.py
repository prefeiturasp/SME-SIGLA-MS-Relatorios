"""Módulo services/base/utils."""

from __future__ import annotations

from typing import Any

from django.conf import settings


def ajustar_logo_caminho(logo: Any) -> Any:
    """Executa ajustar logo caminho.

    Args:
        logo: Parâmetro logo.

    Returns:
        Resultado da operação.

    Raises:
        Nenhuma exceção específica documentada.
    """
    if logo and isinstance(logo, str):
        if settings.DJANGO_ENVIRONMENT != "local":
            base_prefix = settings.MS_PATH.rstrip("/")
            if base_prefix:
                segment = f"{base_prefix}/media/"
                if "/media/" in logo and segment not in logo:
                    logo = logo.replace("/media/", segment, 1)
        return logo
    return None
