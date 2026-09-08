from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create or reset the local demo doctor account.'

    def handle(self, *args, **options):
        user_model = get_user_model()
        doctor, created = user_model.objects.get_or_create(
            username='doctor',
            defaults={
                'first_name': 'Doctor',
                'last_name': 'Demo',
                'email': 'doctor@example.com',
            },
        )
        doctor.set_password('Doctor@123')
        doctor.is_active = True
        doctor.is_staff = False
        doctor.is_superuser = False
        doctor.save(update_fields=[
            'password',
            'is_active',
            'is_staff',
            'is_superuser',
        ])

        action = 'Created' if created else 'Reset'
        self.stdout.write(self.style.SUCCESS(
            f'{action} demo doctor account: username=doctor, active=True'
        ))
