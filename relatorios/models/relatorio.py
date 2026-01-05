from django.db import models
from auditlog.registry import auditlog
from .base import BaseModel
from .constants import TIPOS_RELATORIOS

class Relatorio(BaseModel):
    """
    Modelo para representar relatórios gerados no sistema.
    """

    tipo = models.CharField(max_length=200, verbose_name="Tipo de Relatório", choices=TIPOS_RELATORIOS)
    usuario = models.CharField(max_length=20, verbose_name="Usuário")
    dados = models.JSONField(max_length=20000, verbose_name="JSON do Relatório", default={})
    processo_uuid = models.UUIDField(verbose_name="UUID do Processo")
    cabecalho = models.CharField(max_length=255, verbose_name="Cabeçalho do Relatório", blank=True, null=True)

    class Meta:
        verbose_name = "Relatório"
        verbose_name_plural = "Relatórios"
        ordering = ['-criado_em']
        db_table = 'relatorios'
    
    def __str__(self):
        return f"{self.tipo} - {self.criado_em}"

auditlog.register(Relatorio)