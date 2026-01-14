import logging
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from relatorios.models import Relatorio
from relatorios.serializers import RelatorioCreateSerializer, RelatorioSerializer
from relatorios.services.factory.relatorio_factory import RelatorioFactory
from relatorios.utils import CustomPagination

logger = logging.getLogger(__name__)


class RelatorioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar relatorios.
    """
    queryset = Relatorio.objects.all()
    serializer_class = RelatorioSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tipo']
    search_fields = ['tipo']
    ordering_fields = ['criado_em']
    ordering = ['-criado_em']
    pagination_class = CustomPagination

    def create(self, request, *args, **kwargs):
        serializer = RelatorioCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tipo_relatorio = serializer.validated_data.get('tipo')
        processo_uuid = serializer.validated_data.get('processo_uuid')
        # Prioriza o cabecalho vindo do request (body ou query), senão usa o validado
        cabecalho = (
            request.data.get('cabecalho')
            or request.query_params.get('cabecalho')
            or serializer.validated_data.get('cabecalho', '')
        )
        usuario = serializer.validated_data.get('usuario', '')
        candidatos_uuids = serializer.validated_data.get('candidatos_uuids', None)

        format_param = request.query_params.get('formato', '').lower()
        accept_header = request.META.get('HTTP_ACCEPT', '')

        # Determinar formato: xls, pdf, docx ou html (padrão)
        if format_param == 'xls' or format_param == 'xlsx' or 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in accept_header:
            formato = 'xls'
        elif format_param == 'pdf' or 'application/pdf' in accept_header:
            formato = 'pdf'
        elif format_param == 'docx' or format_param == 'doc' or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in accept_header:
            formato = 'docx'
        else:
            formato = 'html'

        logger.info('Tipo de relatório: %s, Formato solicitado: %s', 
                   tipo_relatorio, formato)

        # Usar Factory para obter a instância correta do relatório
        try:
            relatorio_service = RelatorioFactory.obter_relatorio(tipo_relatorio)
            response, dados = relatorio_service.gerar(
                processo_uuid,
                request,
                formato,
                cabecalho,
                candidatos_uuids=candidatos_uuids
            )
            try:
                serializer.save(dados=dados)
                logger.info('Relatório salvo no banco de dados - tipo: %s, usuario: %s', tipo_relatorio, usuario)
            except Exception as exc:
                logger.error('Erro ao salvar relatório no banco de dados: %s', exc, exc_info=True)

            return response

        except ValueError as exc:
            logger.error('Tipo de relatório inválido: %s - %s', tipo_relatorio, exc)
            return Response(
                {'error': str(exc)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as exc:
            logger.error('Erro ao gerar relatório do tipo %s: %s', tipo_relatorio, exc, exc_info=True)
            return Response(
                {'error': f'Erro ao gerar relatório: {str(exc)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
