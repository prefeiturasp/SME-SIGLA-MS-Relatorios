import logging

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
    """
    ViewSet para gerenciar parametrização de relatórios.
    Sempre trabalha com o registro mais recente.
    """

    queryset = Parametrizacao.objects.all().order_by("-criado_em")
    serializer_class = ParametrizacaoSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_object(self):
        """Sempre retorna o registro mais recente, ignorando o pk."""
        return self.queryset.first()

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": 'Method "POST" not allowed.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )
