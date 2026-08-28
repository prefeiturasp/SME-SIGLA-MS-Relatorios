"""Repositórios de acesso a dados do app relatorios."""

from __future__ import annotations

from typing import Any

from relatorios.models import ConfiguracaoRelatorio, Parametrizacao, Relatorio


class ParametrizacaoRepository:
    """Consultas e persistência de parametrização de relatórios."""

    @staticmethod
    def obter_mais_recente() -> Parametrizacao | None:
        """Retorna a parametrização mais recente (padrão singleton) ou None."""
        return Parametrizacao.objects.order_by("-criado_em").first()


class ConfiguracaoRelatorioRepository:
    """Consultas de configuração de relatórios."""

    @staticmethod
    def obter_por_tipo(tipo: str) -> ConfiguracaoRelatorio:
        """Retorna a configuração do tipo informado.

        Raises:
            ConfiguracaoRelatorio.DoesNotExist: Se não houver configuração
                cadastrada para o tipo.
        """
        return ConfiguracaoRelatorio.objects.get(tipo=tipo)


class RelatorioRepository:
    """Consultas e persistência de relatórios gerados."""

    @classmethod
    def atualizar(cls, instancia: Relatorio, **campos: Any) -> None:
        """Atualiza os campos informados na instância e persiste."""
        for campo, valor in campos.items():
            setattr(instancia, campo, valor)
        instancia.save(update_fields=list(campos.keys()))

    @staticmethod
    def contar() -> int:
        """Conta o total de relatórios existentes."""
        return Relatorio.objects.count()

    @staticmethod
    def excluir_todos() -> int:
        """Remove todos os relatórios.

        Returns:
            Quantidade de registros removidos.
        """
        quantidade, _ = Relatorio.objects.all().delete()
        return quantidade
