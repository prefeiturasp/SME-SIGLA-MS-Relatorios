"""Django management command to create sample relatorios."""
from __future__ import annotations
from typing import Any
import random
from django.core.management.base import BaseCommand
from relatorios.models import Relatorio

class Command(BaseCommand):
    """Define Command."""
    help = 'Cria relatórios de exemplo para desenvolvimento'

    def add_arguments(self, parser: Any) -> None:
        """Registra argumentos da linha de comando."""
        parser.add_argument('--count', type=int, default=5, help='Número de relatórios a serem criados (padrão: 5)')

    def handle(self, *args: Any, **options: Any) -> None:
        """Executa a lógica principal do comando."""
        count = options['count']
        self.stdout.write(self.style.SUCCESS(f'Criando {count} relatórios...'))
        tipos = ['agenda', 'convocacao', 'selecao', 'avaliacao']
        criados = []
        for i in range(count):
            item = Relatorio.objects.create(nome=f'Relatório {i + 1}', tipo=random.choice(tipos))  # type: ignore[misc]
            criados.append(item)
            self.stdout.write(f'  ✓ Criado: {item.nome} ({item.tipo})')  # type: ignore[attr-defined]
        self.stdout.write(self.style.SUCCESS(f'✅ {len(criados)} relatórios criados com sucesso!'))
