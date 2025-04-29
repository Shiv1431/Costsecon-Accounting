from django.core.management.base import BaseCommand
from django.utils import timezone
from core.views import send_consultation_reminders

class Command(BaseCommand):
    help = 'Sends reminder emails for consultations scheduled for tomorrow'

    def handle(self, *args, **options):
        send_consultation_reminders()
        self.stdout.write(self.style.SUCCESS('Successfully sent reminder emails')) 