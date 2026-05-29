"""
Django management command to clear all relatorios.
"""

from django.core.management.base import BaseCommand

from relatorios.models import Relatorio


class Command(BaseCommand):
    help = "Remove todos os registros da tabela de relatórios"

    def handle(self, *args, **options):
        total = Relatorio.objects.count()

        self.stdout.write(
            self.style.SUCCESS(f"Removendo {total} relatórios...")
        )

        try:
            if total > 0:
                Relatorio.objects.all().delete()
                self.stdout.write(
                    self.style.SUCCESS(f"✅ {total} relatórios removidos!")
                )

            restantes = Relatorio.objects.count()
            if restantes == 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        "✅ Tabela de relatórios completamente limpa!"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  Ainda restam {restantes} relatórios."
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Erro ao remover registros: {e}")
            )
