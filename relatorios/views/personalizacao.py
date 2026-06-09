"""Módulo views/personalizacao."""
from __future__ import annotations
from typing import Any
import logging
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from relatorios.models import ConfiguracaoRelatorio
from relatorios.serializers import ConfiguracaoRelatorioSerializer
logger = logging.getLogger(__name__)

class PersonalizacaoViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """ViewSet para gerenciar personalização de relatórios."""
    queryset = ConfiguracaoRelatorio.objects.all()
    serializer_class = ConfiguracaoRelatorioSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tipo']
    search_fields = ['tipo']
    ordering_fields = ['criado_em']
    ordering = ['-criado_em']
    lookup_field = 'uuid'

    def list(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        """GET /personalizacao/?processo_uuid=...&tipo=...
        
        Args:
            self: Instância do objeto.
            request: Requisição HTTP recebida.
            *args: Argumentos posicionais variáveis.
            **kwargs: Argumentos nomeados variáveis.
        
        Returns:
            Resposta HTTP com os dados serializados.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        resultado = self.filter_queryset(self.get_queryset())[0] if self.filter_queryset(self.get_queryset()) else None
        serializer = self.get_serializer(resultado)
        data = serializer.data
        return Response(data)
