from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create or reset the local demo administrator account.'

    def handle(self, *args, **options):
        user_model = get_user_model()
        admin_user, created = user_model.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Application',
                'last_name': 'Administrator',
                'email': 'admin@example.com',
            },
        )
        admin_user.set_password('Admin@123')
        admin_user.is_active = True
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save(update_fields=[
            'password',
            'is_active',
            'is_staff',
            'is_superuser',
        ])

        action = 'Created' if created else 'Reset'
        self.stdout.write(self.style.SUCCESS(
            f'{action} demo administrator account: username=admin, active=True'
        ))
