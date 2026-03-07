from django.core.management.base import BaseCommand

from tsc_api.registry.models import Country, FindingCatalog, System


class Command(BaseCommand):
    help = 'Seed initial catalogs for systems, countries, and findings.'

    def handle(self, *args, **options):
        systems = [
            ('BRAIN', 'Brain'),
            ('HEART', 'Heart'),
            ('KIDNEY', 'Kidney'),
            ('SKIN', 'Skin'),
            ('LUNG', 'Lung'),
            ('SEIZURES', 'Seizures'),
        ]
        for code, name in systems:
            System.objects.update_or_create(system_code=code, defaults={'system_name': name})

        countries = [('US', 'United States'), ('MX', 'Mexico'), ('CO', 'Colombia')]
        for code, name in countries:
            Country.objects.update_or_create(country_code=code, defaults={'country_name': name})

        findings = [
            ('SEGA', 'BRAIN', 'Subependymal giant cell astrocytoma'),
            ('AML', 'KIDNEY', 'Angiomyolipoma'),
            ('RHAB', 'HEART', 'Cardiac rhabdomyoma'),
        ]
        for code, system_code, name in findings:
            FindingCatalog.objects.update_or_create(
                finding_code=code,
                defaults={
                    'system_id': system_code,
                    'finding_name': name,
                    'description': name,
                    'is_active': True,
                },
            )

        self.stdout.write(self.style.SUCCESS('Catalogs seeded successfully.'))
