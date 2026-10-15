"""Módulo views/parametrizacao."""

from __future__ import annotations

import logging
from typing import Any

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from relatorios.api.schemas.parametrizacao import (
    OPERACOES_PARAMETRIZACAO,
    TAG_PARAMETRIZACAO,
)
from relatorios.models import Parametrizacao
from relatorios.repository import ParametrizacaoRepository
from relatorios.serializers import ParametrizacaoSerializer

logger = logging.getLogger(__name__)


@extend_schema(tags=[TAG_PARAMETRIZACAO])
@extend_schema_view(**OPERACOES_PARAMETRIZACAO)
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

        Returns:
            Resposta HTTP com os dados solicitados.
        """
        return ParametrizacaoRepository.obter_mais_recente()

    def create(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        """Create.

        Args:
            request: Requisição HTTP recebida.
            *args: Argumentos posicionais repassados ao comando.
            **kwargs: Argumentos nomeados repassados ao comando.

        Returns:
            Resposta HTTP com os dados serializados.
        """
        return Response(
            {"detail": 'Method "POST" not allowed.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
