import uuid
from rest_framework import serializers
from ..models import Relatorio
from ..models.constants import TIPOS_RELATORIOS


class RelatorioCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação de relatórios com validação de campos obrigatórios.
    O campo 'dados' não é validado no is_valid(), apenas setado no save().
    """

    usuario = serializers.CharField(required=True, help_text="RF do usuário")
    processo_uuid = serializers.UUIDField(required=True, help_text="UUID do processo")
    cabecalho = serializers.CharField(required=False, allow_blank=True, help_text="Cabeçalho do relatório (opcional)")
    candidatos_uuids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        help_text="Lista opcional de UUIDs de candidatos"
    )

    class Meta:
        model = Relatorio
        fields = [     
            'tipo',
            'usuario',
            'processo_uuid',
            'cabecalho',
            'candidatos_uuids',
        ]

    def validate_tipo(self, value):
        """
        Valida se o tipo do relatório é válido.
        """
        tipos_validos = [choice[0] for choice in TIPOS_RELATORIOS]
        if value not in tipos_validos:
            raise serializers.ValidationError(
                f"Tipo inválido. Tipos válidos: {', '.join(tipos_validos)}"
            )
        return value

    def save(self, dados=None, **kwargs):
        """
        Salva o relatório no banco de dados.
        O campo 'dados' é setado aqui, não sendo validado no is_valid().

        Args:
            dados: Dados do relatório a serem salvos (opcional)
            **kwargs: Outros campos que podem ser passados (processo_uuid, cabecalho, etc.)
        """
        # Chamar o save() do ModelSerializer para criar/atualizar a instância
        # Os campos validados (tipo, usuario, processo_uuid, cabecalho) serão salvos automaticamente
        relatorio = super().save(**kwargs)

        if dados is not None:
            relatorio.dados = dados
            relatorio.save(update_fields=['dados'])

        return relatorio
