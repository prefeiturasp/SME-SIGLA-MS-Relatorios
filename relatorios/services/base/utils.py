"""Módulo services/base/utils."""

from __future__ import annotations

from typing import Any

from django.conf import settings


def ajustar_logo_caminho(logo: Any) -> Any:
    """Ajustar logo caminho.

    Args:
        logo: Logo.

    Returns:
        Quantidade ou código numérico resultante.
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
