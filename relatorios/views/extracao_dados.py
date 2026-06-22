"""
View para extração de dados agregados de microserviços.
"""

import logging

from requests import RequestException
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from relatorios.serializers.extracao_dados import ExtracaoDadosQuerySerializer
from relatorios.services.extracao_dados_service import ExtracaoDadosService

logger = logging.getLogger(__name__)


class ExtracaoDadosViewSet(viewsets.GenericViewSet):
    """
    ViewSet para extração de dados.

    GET /extracao-dados/          → list (filtrado por concurso_uuid e ano)
    GET /extracao-dados/total/    → action total (extração geral)
    """

    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        serializer = ExtracaoDadosQuerySerializer(
            data=ExtracaoDadosQuerySerializer.normalize_query_data(
                request.query_params
            )
        )
        serializer.is_valid(raise_exception=True)

        concurso_uuid = str(serializer.validated_data["concurso_uuid"])
        anos = sorted(serializer.validated_data["ano"])

        try:
            dados = ExtracaoDadosService().extrair(
                concurso_uuid=concurso_uuid,
                anos=anos,
            )
        except RequestException as exc:
            logger.error(
                "Erro ao extrair dados (concurso_uuid=%s, anos=%s): %s",
                concurso_uuid,
                anos,
                exc,
            )
            return Response(
                {"detail": "Erro ao comunicar com serviço externo."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(dados, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="total")
    def total(self, request, *args, **kwargs):
        try:
            dados = ExtracaoDadosService().extrair_total()
        except RequestException as exc:
            logger.error("Erro ao extrair dados gerais: %s", exc)
            return Response(
                {"detail": "Erro ao comunicar com serviço externo."},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response(dados, status=status.HTTP_200_OK)
