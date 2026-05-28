from auditlog.registry import auditlog
from django.db import models

from .base import BaseModel
from .constants import TIPOS_RELATORIOS


class ConfiguracaoRelatorio(BaseModel):
    """
    Modelo para representar configurações específicas de cada tipo de
    relatório.
    """

    tipo = models.CharField(
        max_length=200,
        verbose_name="Tipo de Relatório",
        choices=TIPOS_RELATORIOS,
        unique=True,
    )
    usar_logotipo = models.BooleanField(
        verbose_name="Usar Logotipo", default=False
    )
    cabecalho = models.TextField(
        verbose_name="Cabeçalho", default="", blank=True
    )
    cabecalho_gabarito = models.TextField(
        verbose_name="Cabeçalho Gabarito", default="", blank=True
    )
    texto_final = models.TextField(
        verbose_name="Texto Final", default="", blank=True
    )

    cabecalho_capa_ata = models.TextField(
        verbose_name="Cabeçalho Capa da Ata", default="", blank=True
    )

    class Meta:
        verbose_name = "Configuração de Relatório"
        verbose_name_plural = "Configurações de Relatórios"
        ordering = ["tipo"]
        db_table = "relatorios_configuracao"

    def __str__(self):
        return f"Configuração - {self.get_tipo_display()}"


auditlog.register(ConfiguracaoRelatorio)
