import os

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.mail import mail_admins
from rest_framework.authtoken.models import Token

from config.utils import set_settings

class Command(BaseCommand):
    help = 'Create DRF Token for integration user'

    def create_token(self, reset_token): 
        user, _ = User.objects.get_or_create(
            username='integration_user'
        )
        if reset_token: 
            Token.objects.filter(user=user).delete() 
        token, created = Token.objects.get_or_create(user=user)
        if created:
            set_settings('integration_user_token', token.key)
            mail_admins(
                'Client-App-{} Integration User - Token Reset'.format(os.getenv('ENV', 'local')),
                'Integration user token reset to: {}'.format(token.key)
            )
        return token

    def add_arguments(self, parser):
        parser.add_argument(
            '-r',
            '--reset',
            action='store_true',
            dest='reset_token',
            default=False,
            help='Reset Integration User Token',
        )

    def handle(self, *args, **options):
        reset_token = options['reset_token']
        token = self.create_token(reset_token) 
        if reset_token:
            self.stdout.write('Token Reset!')
        self.stdout.write('Generated token {0} for integration user'.format(token.key))