"""Módulo serializers/relatorio_create."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from relatorios.models import Relatorio
from relatorios.models.constants import TIPOS_RELATORIOS
from relatorios.repository import RelatorioRepository


class RelatorioCreateSerializer(serializers.ModelSerializer):
    """Dados que identificam o relatório a gerar e ficam no histórico."""

    usuario = serializers.CharField(
        required=True,
        help_text="RF do usuário que pediu o relatório. Fica no histórico.",
    )
    processo_uuid = serializers.UUIDField(
        required=True,
        help_text="UUID do processo de convocação cujos dados são lidos.",
    )
    cabecalho = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=(
            "Cabeçalho informado no pedido, em HTML. Vai só para o "
            "histórico: o relatório usa os textos da personalização e da "
            "parametrização. Se, sem as tags, o texto fica vazio, é "
            "gravado vazio."
        ),
    )
    agenda_uuid = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=(
            "UUID da agenda (sessão de escolha). Só é usado em "
            "`LISTA_CANDIDATOS_SESSAO`, para listar uma única sessão. Se "
            "vier vazio ou não for um UUID, o relatório é gerado, mas o "
            "histórico não é gravado."
        ),
    )

    class Meta:
        """Representa Meta."""

        model = Relatorio
        fields = [
            "tipo",
            "usuario",
            "processo_uuid",
            "cabecalho",
            "agenda_uuid",
        ]
        extra_kwargs = {
            "tipo": {"help_text": "Tipo de relatório a gerar."},
        }

    def validate_tipo(self, value: Any) -> Any:
        """Valida tipo."""
        tipos_validos = [choice[0] for choice in TIPOS_RELATORIOS]
        if value not in tipos_validos:
            raise serializers.ValidationError(
                f"Tipo inválido. Tipos válidos: {', '.join(tipos_validos)}"
            )
        return value

    def validate_cabecalho(self, value: str) -> str:
        """Valida cabecalho."""
        try:
            from django.utils.html import strip_tags as _strip

            texto = _strip(value or "").replace("&nbsp;", " ").strip()
            if not texto:
                return ""
            return value
        except Exception:
            return value

    def save(self, dados: Any = None, **kwargs: Any) -> Any:
        """Persiste o relatório e atualiza os dados quando informados."""
        relatorio = super().save(**kwargs)
        if dados is not None:
            RelatorioRepository.atualizar(relatorio, dados=dados)
        return relatorio


# Só para a documentação: a view valida com ``RelatorioCreateSerializer`` e
# lê ``cargo_codigo`` direto do corpo da requisição.
class GeracaoRelatorioSerializer(RelatorioCreateSerializer):
    """Pedido de geração de um relatório."""

    cargo_codigo = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text=(
            'Código do cargo, como texto (por exemplo `"3859"`). Só é '
            "usado em `ATA_ESCOLHA`, e só quando o processo tem agendas de "
            "mais de um cargo: sem ele, a resposta é 400 com a lista "
            "`cargos`. Envie o valor como veio nessa lista; o número "
            "`3859` não é aceito no lugar do texto."
        ),
    )

    class Meta(RelatorioCreateSerializer.Meta):
        """Campos validados mais o que a view lê direto do corpo."""

        fields = [*RelatorioCreateSerializer.Meta.fields, "cargo_codigo"]
