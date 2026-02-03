from django.db import models
from .base import BaseModel


class Parametrizacao(BaseModel):
    """
    Model para gerenciar parâmetros de relatórios.
    Armazena o cabeçalho padrão (HTML) e a logo para os relatórios.
    """
    cabecalho = models.TextField(
        default="",
        blank=True,
        verbose_name="Cabeçalho Padrão",
        help_text="Cabeçalho padrão em HTML para os relatórios"
    )
    logo = models.ImageField(
        upload_to='parametrizacao/',
        null=True,
        blank=True,
        verbose_name="Logo",
        help_text="Logo para os relatórios"
    )

    class Meta:
        verbose_name = 'Parametrização'
        verbose_name_plural = 'Parametrizações'
        ordering = ['-criado_em']

    def __str__(self):
        return f"Parametrização - Criado em {self.criado_em}"
