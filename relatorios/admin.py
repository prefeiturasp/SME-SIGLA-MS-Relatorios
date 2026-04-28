"""
Django admin configuration for the processes module.
"""
from django.contrib import admin
from .models import Relatorio, Parametrizacao, ConfiguracaoRelatorio


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
            'fields': ('tipo', 'usuario', 'processo_uuid', 'agenda_uuid')
        }),
        ('Configurações', {
            'fields': ('cabecalho', 'usou_cabecalho_padrao', 'usou_logotipo', 'texto_final')
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em')
        }),
        ('Metadados', {
            'fields': ('uuid',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Parametrizacao)
class ParametrizacaoAdmin(admin.ModelAdmin):
    """Admin for Parametrizacao model."""

    list_display = (
        'uuid', 'criado_em', 'atualizado_em',
    )
    readonly_fields = ('uuid', 'criado_em', 'atualizado_em')
    ordering = ('-criado_em',)

    fieldsets = (
        ('Parametrização', {
            'fields': ('cabecalho', 'logo')
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em')
        }),
        ('Metadados', {
            'fields': ('uuid',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ConfiguracaoRelatorio)
class ConfiguracaoRelatorioAdmin(admin.ModelAdmin):
    """Admin for ConfiguracaoRelatorio model."""

    list_display = (
        'tipo', 'usar_logotipo', 'criado_em'
    )
    list_filter = ('tipo', 'usar_logotipo')
    search_fields = ('tipo', 'cabecalho', 'texto_final')
    readonly_fields = ('uuid', 'criado_em', 'atualizado_em')
    ordering = ('tipo',)

    fieldsets = (
        ('Configuração', {
            'fields': ('tipo', 'usar_logotipo')
        }),
        ('Conteúdo', {
            'fields': ('cabecalho', 'texto_final')
        }),
        ('Datas', {
            'fields': ('criado_em', 'atualizado_em')
        }),
        ('Metadados', {
            'fields': ('uuid',),
            'classes': ('collapse',)
        }),
    )
