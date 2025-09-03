"""
Django admin configuration for the processes module.
"""
from django.contrib import admin
from .models import Relatorio


@admin.register(Relatorio)
class RelatorioAdmin(admin.ModelAdmin):
    """Admin for Relatorio model."""

    list_display = (
        'nome', 'tipo',
    )
    list_filter = ('tipo',)
    search_fields = ('nome', 'tipo')
    readonly_fields = ('uuid', 'criado_em', 'atualizado_em')
    ordering = ('-criado_em',)

    fieldsets = (
        ('Relatório', {
            'fields': ('nome', 'tipo')
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em')
        }),
        ('Metadados', {
            'fields': ('uuid',),
            'classes': ('collapse',)
        }),
    )
