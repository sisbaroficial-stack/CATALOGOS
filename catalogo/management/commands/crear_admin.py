import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Crea o actualiza el superusuario inicial usando ADMIN_EMAIL y ADMIN_PASSWORD.'

    def handle(self, *args, **options):
        email = os.getenv('ADMIN_EMAIL', '').strip()
        password = os.getenv('ADMIN_PASSWORD', '')
        if not email or not password:
            self.stdout.write('ADMIN_EMAIL y ADMIN_PASSWORD no están configurados; se omite crear_admin.')
            return

        user_model = get_user_model()
        username_field = user_model.USERNAME_FIELD
        lookup = {username_field: email}
        defaults = {'is_staff': True, 'is_superuser': True}
        if username_field != 'email' and any(field.name == 'email' for field in user_model._meta.fields):
            defaults['email'] = email

        user, created = user_model.objects.get_or_create(defaults=defaults, **lookup)
        changed = created
        if not user.is_staff:
            user.is_staff = True
            changed = True
        if not user.is_superuser:
            user.is_superuser = True
            changed = True
        if created or not user.check_password(password):
            user.set_password(password)
            changed = True
        if changed:
            user.save()

        action = 'creado' if created else 'actualizado'
        self.stdout.write(self.style.SUCCESS(f'Superusuario {action}: {email}'))
