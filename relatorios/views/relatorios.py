from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from relatorios.models import Relatorio
from relatorios.serializers import (
    RelatorioSerializer,
)
from relatorios.utils import CustomPagination


class RelatorioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar relatorios.
    """
    queryset = Relatorio.objects.all()
    serializer_class = RelatorioSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tipo']
    search_fields = ['nome', 'tipo']
    ordering_fields = ['criado_em']
    ordering = ['-criado_em']
    pagination_class = CustomPagination
