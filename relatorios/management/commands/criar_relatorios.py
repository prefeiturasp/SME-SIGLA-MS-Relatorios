"""
Django management command to create sample relatorios.
"""
from django.core.management.base import BaseCommand
from relatorios.models import Relatorio
import random


class Command(BaseCommand):
    help = 'Cria relatórios de exemplo para desenvolvimento'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Número de relatórios a serem criados (padrão: 5)'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        self.stdout.write(
            self.style.SUCCESS(f'Criando {count} relatórios...')
        )
        
        tipos = ["agenda", "convocacao", "selecao", "avaliacao"]
        criados = []

        for i in range(count):
            item = Relatorio.objects.create(
                nome=f"Relatório {i+1}",
                tipo=random.choice(tipos),
            )
            criados.append(item)
            self.stdout.write(f"  ✓ Criado: {item.nome} ({item.tipo})")

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ {len(criados)} relatórios criados com sucesso!'
            )
        ) 