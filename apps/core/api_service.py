"""Base comum para clientes HTTP de microserviços externos."""

from __future__ import annotations

from django.conf import settings


class BaseApiService:
    """Configuração compartilhada de URL base, timeout e headers JSON."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: int = 30,
        api_key: str | None = None,
    ) -> None:
        """Inicializa cliente com URL base, timeout e chave de API.

        Args:
            base_url: URL base do serviço remoto.
            timeout_seconds: Tempo máximo de espera, em segundos.
            api_key: Chave de API enviada no header de autenticação entre
                microsserviços, quando informada.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if api_key:
            self._headers[settings.API_KEY_HEADER] = api_key
