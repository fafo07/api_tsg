from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone

from tsc_api.registry.models import RegistryUser, Role


class Command(BaseCommand):
    help = 'Seed default admin role and admin user.'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin')
        parser.add_argument('--email', default='admin@example.com')
        parser.add_argument('--password', default='admin123')

    def handle(self, *args, **options):
        role, _ = Role.objects.update_or_create(role_name='ADMIN', defaults={})

        RegistryUser.objects.update_or_create(
            username=options['username'],
            defaults={
                'email': options['email'],
                'password_hash': make_password(options['password']),
                'role': role,
                'is_active': True,
                'created_at': timezone.now(),
            },
        )

        self.stdout.write(self.style.SUCCESS('Admin user seeded successfully.'))
