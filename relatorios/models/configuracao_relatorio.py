from django.db import models
from auditlog.registry import auditlog
from .base import BaseModel
from .constants import TIPOS_RELATORIOS


class ConfiguracaoRelatorio(BaseModel):
    """
    Modelo para representar configurações específicas de cada tipo de relatório.
    """
    
    tipo = models.CharField(
        max_length=200,
        verbose_name="Tipo de Relatório",
        choices=TIPOS_RELATORIOS,
        unique=True
    )
    usar_logotipo = models.BooleanField(
        verbose_name="Usar Logotipo",
        default=False
    )
    usar_cabecalho_padrao = models.BooleanField(
        verbose_name="Usar Cabeçalho Padrão",
        default=False
    )
    cabecalho = models.CharField(
        max_length=500,
        verbose_name="Cabeçalho",
        default="",
        blank=True
    )
    texto_final = models.CharField(
        max_length=1000,
        verbose_name="Texto Final",
        default="",
        blank=True
    )
    
    class Meta:
        verbose_name = "Configuração de Relatório"
        verbose_name_plural = "Configurações de Relatórios"
        ordering = ['tipo']
        db_table = 'configuracao_relatorio'
    
    def __str__(self):
        return f"Configuração - {self.get_tipo_display()}"


auditlog.register(ConfiguracaoRelatorio)
