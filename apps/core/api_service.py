"""Base comum para clientes HTTP de microserviços externos."""

from __future__ import annotations


class BaseApiService:
    """Configuração compartilhada de URL base, timeout e headers JSON."""

    def __init__(self, base_url: str, timeout_seconds: int = 30) -> None:
        """Inicializa cliente com URL base e timeout.

        Args:
            base_url: URL base do serviço remoto.
            timeout_seconds: Tempo máximo de espera, em segundos.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
