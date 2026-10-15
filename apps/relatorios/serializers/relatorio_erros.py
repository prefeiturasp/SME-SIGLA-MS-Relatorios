"""Corpos de erro próprios da geração de relatórios."""

from rest_framework import serializers


class ErroRelatorioSerializer(serializers.Serializer):
    """Falha ao gerar o relatório."""

    error = serializers.CharField(
        help_text=(
            "Mensagem da falha. Quando ela vem de outro microsserviço, traz "
            "o texto técnico da chamada que falhou."
        )
    )


class CargoDoProcessoSerializer(serializers.Serializer):
    """Cargo que tem agenda no processo de convocação."""

    cargo_codigo = serializers.CharField(
        help_text=(
            "Código do cargo, como texto. É o valor a enviar em "
            "`cargo_codigo` para gerar a Ata de Escolha."
        )
    )
    cargo_nome = serializers.CharField(help_text="Nome do cargo.")


class CargoObrigatorioSerializer(serializers.Serializer):
    """Aviso de que a Ata de Escolha precisa do cargo."""

    error = serializers.CharField(
        help_text="Mensagem que pede a escolha de um cargo."
    )
    cargos = CargoDoProcessoSerializer(
        many=True,
        help_text="Cargos com agenda no processo, para escolher um.",
    )
