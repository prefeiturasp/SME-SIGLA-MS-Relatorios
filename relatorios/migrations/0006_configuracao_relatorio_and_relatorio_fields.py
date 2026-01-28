# Generated migration

import uuid
from django.db import migrations, models


def popular_configuracao_relatorio(apps, schema_editor):
    """Cria um registro de configuração para cada tipo de relatório."""
    ConfiguracaoRelatorio = apps.get_model('relatorios', 'ConfiguracaoRelatorio')
    
    # Lista de tipos de relatórios
    tipos_relatorios = [
        'LAUDA_VAGAS',
        'RELACAO_VAGAS',
        'SUMULA_NAO_ESCOLHAS',
        'LISTAGEM_ESCOLHAS_DRES',
        'SUMULA_RECONVOCACAO',
        'SUMULA_ESCOLHAS',
        'RECONVOCACAO',
        'LAUDA_CONVOCACAO',
        'RESULTADO_ESCOLHA_SIM',
        'RESULTADO_ESCOLHA_NAO',
        'RESULTADO_ESCOLHA_RECONVOCACAO',
        'LISTA_CANDIDATOS_SESSAO',
        'ATA_ESCOLHA',
    ]
    
    # Cria um registro para cada tipo de relatório
    for tipo in tipos_relatorios:
        ConfiguracaoRelatorio.objects.get_or_create(
            tipo=tipo,
            defaults={
                'usar_logotipo': False,
                'usar_cabecalho_padrao': False,
                'cabecalho': '',
                'texto_final': '',
            }
        )


def reverter_popular_configuracao_relatorio(apps, schema_editor):
    """Remove todos os registros de configuração de relatórios."""
    ConfiguracaoRelatorio = apps.get_model('relatorios', 'ConfiguracaoRelatorio')
    ConfiguracaoRelatorio.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('relatorios', '0005_parametrizacao_relatorio_id_alter_relatorio_tipo_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfiguracaoRelatorio',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'uuid',
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                (
                    'criado_em',
                    models.DateTimeField(
                        auto_now_add=True, verbose_name='Data de Criação'
                    ),
                ),
                (
                    'atualizado_em',
                    models.DateTimeField(
                        auto_now=True, verbose_name='Data de Atualização'
                    ),
                ),
                (
                    'tipo',
                    models.CharField(
                        choices=[
                            ('LAUDA_VAGAS', 'Lauda de Vagas'),
                            ('RELACAO_VAGAS', 'Relação de Vagas'),
                            ('SUMULA_NAO_ESCOLHAS', 'Relatório de Não Escolhas'),
                            ('LISTAGEM_ESCOLHAS_DRES', 'Listagem de Escolhas por DREs'),
                            ('SUMULA_RECONVOCACAO', 'Súmula de Reconvocados'),
                            ('SUMULA_ESCOLHAS', 'Súmula de Escolhas'),
                            ('RECONVOCACAO', 'Súmula de Reconvocados'),
                            ('LAUDA_CONVOCACAO', 'Lauda de Convocação'),
                            ('RESULTADO_ESCOLHA_SIM', 'Resultado de Escolha de vagas - Sim'),
                            ('RESULTADO_ESCOLHA_NAO', 'Resultado de Escolha de vagas - Não'),
                            ('RESULTADO_ESCOLHA_RECONVOCACAO', 'Resultado de Escolha de vagas - Reconvocação'),
                            ('LISTA_CANDIDATOS_SESSAO', 'Lista de Candidatos por Sessão'),
                            ('ATA_ESCOLHA', 'Ata de Escolha'),
                        ],
                        max_length=200,
                        unique=True,
                        verbose_name='Tipo de Relatório',
                    ),
                ),
                (
                    'usar_logotipo',
                    models.BooleanField(default=False, verbose_name='Usar Logotipo'),
                ),
                (
                    'usar_cabecalho_padrao',
                    models.BooleanField(
                        default=False, verbose_name='Usar Cabeçalho Padrão'
                    ),
                ),
                (
                    'cabecalho',
                    models.CharField(
                        blank=True, default='', max_length=500, verbose_name='Cabeçalho'
                    ),
                ),
                (
                    'texto_final',
                    models.CharField(
                        blank=True,
                        default='',
                        max_length=1000,
                        verbose_name='Texto Final',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Configuração de Relatório',
                'verbose_name_plural': 'Configurações de Relatórios',
                'ordering': ['tipo'],
                'db_table': 'configuracao_relatorio',
            },
        ),
        migrations.AddField(
            model_name='relatorio',
            name='texto_final',
            field=models.TextField(blank=True, null=True, verbose_name='Texto Final'),
        ),
        migrations.AddField(
            model_name='relatorio',
            name='usou_cabecalho_padrao',
            field=models.BooleanField(
                default=False, verbose_name='Usou Cabeçalho Padrão'
            ),
        ),
        migrations.AddField(
            model_name='relatorio',
            name='usou_logotipo',
            field=models.BooleanField(default=False, verbose_name='Usou Logotipo'),
        ),
        migrations.RunPython(
            popular_configuracao_relatorio,
            reverter_popular_configuracao_relatorio
        ),
    ]
