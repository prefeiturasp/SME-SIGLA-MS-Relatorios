"""
Django admin configuration for the processes module.
"""
from django.contrib import admin
from .models import Relatorio


@admin.register(Relatorio)
class RelatorioAdmin(admin.ModelAdmin):
    """Admin for Relatorio model."""

    list_display = (
        'uuid', 'tipo', 'usuario',
    )
    list_filter = ('tipo', 'usuario')
    search_fields = ('tipo', 'usuario')
    readonly_fields = ('uuid', 'criado_em', 'atualizado_em')
    ordering = ('-criado_em',)

    fieldsets = (
        ('Relatório', {
            'fields': ('tipo', 'usuario')
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em')
        }),
        ('Metadados', {
            'fields': ('uuid',),
            'classes': ('collapse',)
        }),
    )
