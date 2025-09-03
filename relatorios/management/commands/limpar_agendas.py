"""
Django management command to clear all agendas.
"""
from django.core.management.base import BaseCommand
from agenda.models import Agenda


class Command(BaseCommand):
    help = 'Remove todos os registros da tabela de agendas'

    def handle(self, *args, **options):
        total_agendas = Agenda.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(f'Removendo {total_agendas} agendas...')
        )
        
        try:
            if total_agendas > 0:
                Agenda.objects.all().delete()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {total_agendas} agendas removidas!')
                )
            
            restantes = Agenda.objects.count()
            if restantes == 0:
                self.stdout.write(
                    self.style.SUCCESS('✅ Tabela de agendas completamente limpa!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Ainda restam {restantes} agendas.'
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao remover registros: {e}')
            ) 