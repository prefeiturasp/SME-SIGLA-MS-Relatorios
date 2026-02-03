import logging
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from relatorios.models import ConfiguracaoRelatorio
from relatorios.serializers import ConfiguracaoRelatorioSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

logger = logging.getLogger(__name__)


class PersonalizacaoViewSet(mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.UpdateModelMixin,
                           viewsets.GenericViewSet):
    """
    ViewSet para gerenciar personalização de relatórios.
    Trabalha com ConfiguracaoRelatorio baseado no tipo de relatório.
    """
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

    # def retrieve(self, request, *args, **kwargs):
    #     """
    #     GET /personalizacao/{uuid}/
    #     Retorna uma configuração específica por UUID.
    #     """
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance)
    #     # Adaptar resposta para o formato esperado pelo frontend
    #     data = serializer.data
    #     data['usar_cabecalho'] = data.get('usar_cabecalho_padrao', False)
    #     data['usar_logotipo'] = data.get('usar_logotipo', False)
    #     return Response(data)
    
    def list(self, request, *args, **kwargs):
        """
        GET /personalizacao/?processo_uuid=...&tipo=...
        Retorna a configuração do tipo de relatório especificado.
        Se não existir, retorna valores padrão.
        """
        resultado = self.filter_queryset(self.get_queryset())[0] if self.filter_queryset(self.get_queryset()) else None
        serializer = self.get_serializer(resultado)
        data = serializer.data
        return Response(data)

    #     try:
    #         configuracao = ConfiguracaoRelatorio.objects.get(tipo=tipo)
    #         serializer = self.get_serializer(configuracao)
    #         # Adaptar resposta para o formato esperado pelo frontend
    #         data = serializer.data
    #         data['usar_cabecalho'] = data.get('usar_cabecalho_padrao', False)
    #         data['usar_logotipo'] = data.get('usar_logotipo', False)
    #         return Response(data)
    #     except ConfiguracaoRelatorio.DoesNotExist:
    #         # Retorna valores padrão se não existir configuração
    #         return Response({
    #             'uuid': None,
    #             'tipo': tipo,
    #             'usar_cabecalho': False,
    #             'usar_logotipo': False,
    #             'usar_cabecalho_padrao': False,
    #             'cabecalho': '',
    #             'texto_final': '',
    #             'criado_em': None,
    #             'atualizado_em': None,
    #         })
    
    # def get_object(self):
    #     """
    #     Retorna o objeto baseado no UUID da URL.
    #     """
    #     pk = self.kwargs.get('pk')
    #     if pk:
    #         return get_object_or_404(ConfiguracaoRelatorio, uuid=pk)
        
    #     # Se não há pk, tenta buscar por tipo (fallback)
    #     tipo = self.request.data.get('tipo') or self.request.query_params.get('tipo')
    #     if tipo:
    #         try:
    #             return ConfiguracaoRelatorio.objects.get(tipo=tipo)
    #         except ConfiguracaoRelatorio.DoesNotExist:
    #             from rest_framework.exceptions import NotFound
    #             raise NotFound('Configuração não encontrada para o tipo especificado.')
        
    #     from rest_framework.exceptions import NotFound
    #     raise NotFound('UUID ou tipo não fornecido.')
    
    # def update(self, request, *args, **kwargs):
    #     """
    #     PATCH /personalizacao/{uuid}/ ou PATCH /personalizacao/
    #     Atualiza ou cria uma configuração de relatório.
    #     """
    #     tipo = request.data.get('tipo', None)
    #     processo_uuid = request.data.get('processo_uuid', None)  # Aceito mas não usado
        
    #     if not tipo:
    #         return Response(
    #             {'detail': 'Campo "tipo" é obrigatório.'},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )
        
    #     # Tentar buscar por UUID primeiro (se fornecido na URL)
    #     configuracao = None
    #     pk = kwargs.get('pk')
    #     if pk:
    #         try:
    #             configuracao = ConfiguracaoRelatorio.objects.get(uuid=pk)
    #         except (ValueError, ConfiguracaoRelatorio.DoesNotExist):
    #             pass
        
    #     # Se não encontrou por UUID, buscar ou criar por tipo
    #     if not configuracao:
    #         configuracao, created = ConfiguracaoRelatorio.objects.get_or_create(
    #             tipo=tipo,
    #             defaults={
    #                 'usar_logotipo': request.data.get('usar_logotipo', False),
    #                 'usar_cabecalho_padrao': request.data.get('usar_cabecalho', False),
    #                 'cabecalho': request.data.get('cabecalho', ''),
    #                 'texto_final': request.data.get('texto_final', ''),
    #             }
    #         )
    #     else:
    #         created = False
        
    #     # Atualizar campos
    #     if 'usar_logotipo' in request.data:
    #         configuracao.usar_logotipo = request.data.get('usar_logotipo', False)
    #     if 'usar_cabecalho' in request.data:
    #         configuracao.usar_cabecalho_padrao = request.data.get('usar_cabecalho', False)
    #     if 'cabecalho' in request.data:
    #         configuracao.cabecalho = request.data.get('cabecalho', '')
    #     if 'texto_final' in request.data:
    #         configuracao.texto_final = request.data.get('texto_final', '')
    #     configuracao.save()
        
    #     serializer = self.get_serializer(configuracao)
    #     # Adaptar resposta para o formato esperado pelo frontend
    #     data = serializer.data
    #     data['usar_cabecalho'] = data.get('usar_cabecalho_padrao', False)
    #     data['usar_logotipo'] = data.get('usar_logotipo', False)
    #     return Response(data)
    
    # def partial_update(self, request, *args, **kwargs):
    #     """Alias para update."""
    #     return self.update(request, *args, **kwargs)

    # @action(detail=False, methods=['patch'], url_path='atualizar')
    # def update_or_create(self, request, *args, **kwargs):
    #     """
    #     PATCH /personalizacao/atualizar/
    #     Atualiza ou cria configuração por tipo (sem UUID na URL).
    #     Usado pelo frontend na primeira gravação, quando ainda não existe uuid.
    #     """
    #     kwargs_without_pk = {**kwargs, 'pk': None}
    #     return self.update(request, *args, **kwargs_without_pk)
