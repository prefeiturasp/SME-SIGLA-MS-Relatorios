"""Serializers compartilhados do projeto."""

from typing import ClassVar

from rest_framework import serializers


class ErroDetalheSerializer(serializers.Serializer):
    """Erro com mensagem única, como o de registro inexistente."""

    detail = serializers.CharField(help_text="Mensagem que descreve o erro.")


class ErrosValidacaoSerializer(serializers.Serializer):
    """Erros de validação no formato padrão do Django REST Framework."""


class MapaComCamposSerializer(serializers.Serializer):
    """Objeto com campos fixos e, além deles, chaves que variam.

    As subclasses declaram os campos fixos como de costume e indicam em
    ``valor_das_chaves`` o modelo do valor de cada chave variável.
    """

    valor_das_chaves: ClassVar[type[serializers.Serializer]]
