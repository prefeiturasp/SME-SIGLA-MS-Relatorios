"""Módulo utils."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

logger = logging.getLogger(__name__)
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10


class CustomPagination(PageNumberPagination):
    """Representa CustomPagination."""

    page = DEFAULT_PAGE  # type: ignore[assignment]
    page_size = DEFAULT_PAGE_SIZE
    page_size_query_param = "page_size"

    def get_paginated_response(self, data: Any) -> Any:
        """Retorna paginated response.

        Args:
            data: Data.

        Returns:
            Valor do campo serializado.
        """
        return Response(
            {
                "links": {
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
                "count": self.page.paginator.count,
                "page": int(self.request.GET.get("page", DEFAULT_PAGE)),
                "page_size": int(
                    self.request.GET.get("page_size", self.page_size)
                ),
                "results": data,
            }
        )  # type: ignore[has-type,union-attr]


def convert_uuids_to_strings(obj: Any) -> Any:
    """Converte UUIDs recursivamente para strings na estrutura informada."""
    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {
            key: convert_uuids_to_strings(value) for key, value in obj.items()
        }
    elif isinstance(obj, list):
        return [convert_uuids_to_strings(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_uuids_to_strings(item) for item in obj)
    else:
        return obj
