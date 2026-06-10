"""Módulo views/parametrizacao."""

from __future__ import annotations

import logging
from typing import Any

from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from relatorios.models import Parametrizacao
from relatorios.serializers import ParametrizacaoSerializer

logger = logging.getLogger(__name__)


class ParametrizacaoViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """ViewSet para gerenciar parametrização de relatórios."""

    queryset = Parametrizacao.objects.all().order_by("-criado_em")
    serializer_class = ParametrizacaoSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_object(self) -> Any:
        """Retorna object.

        Args:
            self: Instância do objeto.

        Returns:
            Valor calculado para o campo ou propriedade.
        """
        return self.queryset.first()

    def create(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        """Create.

        Args:
            self: Instância do objeto.
            request: Requisição HTTP recebida.
            *args: Argumentos posicionais variáveis.
            **kwargs: Argumentos nomeados variáveis.

        Returns:
            Resposta HTTP com os dados serializados.
        """
        return Response(
            {"detail": 'Method "POST" not allowed.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
