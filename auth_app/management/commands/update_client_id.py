import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Update all Users with null client_id to a new uuid'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        # users = User.objects.filter(client_id__isnull=True)
        users = User.objects.all()
        for user in users:
            user.client_id = uuid.uuid4().hex[:6]
            user.save()
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {users.count()} users'))