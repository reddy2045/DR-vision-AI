from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create or reset admin account credentials'

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(username='admin', defaults={
            'email': 'admin@phc.org',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
            'first_name': 'System',
            'last_name': 'Administrator',
        })
        user.set_password('Admin@1234')
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created admin user.'))
        else:
            self.stdout.write(self.style.SUCCESS('Successfully updated admin user password.'))

