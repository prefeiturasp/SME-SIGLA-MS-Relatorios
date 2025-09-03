"""
Django management command to create sample agendas.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from agenda.models import Agenda
import uuid
import random


class Command(BaseCommand):
    help = 'Cria agendas de convocação de exemplo para desenvolvimento'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Número de agendas a serem criadas (padrão: 5)'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        self.stdout.write(
            self.style.SUCCESS(f'Criando {count} agendas...')
        )
        
        processos_disponiveis = [
            {'uuid': uuid.uuid4(), 'nome': 'Processo de Convocação 1'},
            {'uuid': uuid.uuid4(), 'nome': 'Processo de Convocação 2'},
            {'uuid': uuid.uuid4(), 'nome': 'Processo de Convocação 3'},
        ]

        cargos_disponiveis = [
            {'uuid': uuid.uuid4(), 'nome': 'Professor'},
            {'uuid': uuid.uuid4(), 'nome': 'Coordenador'},
            {'uuid': uuid.uuid4(), 'nome': 'Diretor'},
        ]

        agendas_criadas = []

        for _ in range(count):
            processo = random.choice(processos_disponiveis)
            cargo = random.choice(cargos_disponiveis)

            agenda = Agenda.objects.create(
                processo_convocacao_uuid=processo['uuid'],
                processo_convocacao_nome=processo['nome'],
                cargo_uuid=cargo['uuid'],
                cargo_nome=cargo['nome'],
                data_escolha=timezone.now() + timezone.timedelta(days=random.randint(0, 15)),
            )
            agendas_criadas.append(agenda)

            self.stdout.write(
                f'  ✓ Agenda criada: {agenda.processo_convocacao_nome} - {agenda.cargo_nome}'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ {len(agendas_criadas)} agendas criadas com sucesso!'
            )
        ) 