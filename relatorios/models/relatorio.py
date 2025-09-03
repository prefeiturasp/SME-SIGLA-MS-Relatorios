from django.db import models
from django.utils import timezone

from auditlog.registry import auditlog

from .base import BaseModel
from .constants import TIPOS_RELATORIOS


class Relatorio(BaseModel):
    """
    Modelo para representar agendas de convocação.
    """

    nome = models.CharField(max_length=200, verbose_name="Nome do Relatório")
    tipo = models.CharField(max_length=200, verbose_name="Tipo de Relatório", choices=TIPOS_RELATORIOS)

    class Meta:
        verbose_name = "Relatório"
        verbose_name_plural = "Relatórios"
        ordering = ['-criado_em']
        db_table = 'relatorios'
    
    def __str__(self):
        return f"{self.nome} - {self.tipo}"

auditlog.register(Relatorio)
