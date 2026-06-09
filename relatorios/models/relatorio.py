"""Módulo models/relatorio."""

from __future__ import annotations

from typing import Any

from auditlog.registry import auditlog
from django.db import models

from .base import BaseModel
from .constants import TIPOS_RELATORIOS


class Relatorio(BaseModel):
    """Modelo para representar relatórios gerados no sistema."""

    tipo = models.CharField(
        max_length=200,
        verbose_name="Tipo de Relatório",
        choices=TIPOS_RELATORIOS,
    )
    usuario = models.CharField(max_length=20, verbose_name="Usuário")
    dados = models.JSONField(
        max_length=20000, verbose_name="JSON do Relatório", default={}
    )
    processo_uuid = models.UUIDField(verbose_name="UUID do Processo")
    cabecalho = models.CharField(
        max_length=255,
        verbose_name="Cabeçalho do Relatório",
        blank=True,
        null=True,
    )
    agenda_uuid = models.UUIDField(
        verbose_name="UUID da Agenda", blank=True, null=True
    )
    usou_cabecalho_padrao = models.BooleanField(
        verbose_name="Usou Cabeçalho Padrão", default=False
    )
    usou_logotipo = models.BooleanField(
        verbose_name="Usou Logotipo", default=False
    )
    texto_final = models.TextField(
        verbose_name="Texto Final", blank=True, null=True
    )
    cabecalho_capa_ata = models.TextField(
        verbose_name="Cabeçalho Capa da Ata", blank=True, null=True
    )

    class Meta:
        """Define Meta."""

        verbose_name = "Relatório"
        verbose_name_plural = "Relatórios"
        ordering = ["-criado_em"]
        db_table = "relatorios"

    def __str__(self) -> Any:
        """Executa   str  .

        Args:
            self: Instância do objeto.

        Returns:
            Resultado da operação.

        Raises:
            Nenhuma exceção específica documentada.
        """
        return f"{self.tipo} - {self.criado_em}"


auditlog.register(Relatorio)
