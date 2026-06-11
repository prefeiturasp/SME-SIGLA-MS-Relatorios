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
    GET /extracao-dados/todos/    → action todos (extração geral)
    """

    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        serializer = ExtracaoDadosQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        concurso_uuid = str(serializer.validated_data["concurso_uuid"])
        ano = serializer.validated_data["ano"]

        try:
            dados = ExtracaoDadosService().extrair(
                concurso_uuid=concurso_uuid,
                ano=ano,
            )
        except RequestException as exc:
            logger.error(
                "Erro ao extrair dados (concurso_uuid=%s, ano=%s): %s",
                concurso_uuid,
                ano,
                exc,
            )
            return Response(
                {"detail": "Erro ao comunicar com serviço externo."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(dados, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="todos")
    def todos(self, request, *args, **kwargs):
        try:
            dados = ExtracaoDadosService().extrair_todos()
        except RequestException as exc:
            logger.error("Erro ao extrair dados gerais: %s", exc)
            return Response(
                {"detail": "Erro ao comunicar com serviço externo."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(dados, status=status.HTTP_200_OK)
