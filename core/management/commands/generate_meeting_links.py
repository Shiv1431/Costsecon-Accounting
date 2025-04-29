from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Consultation
from datetime import timedelta

class Command(BaseCommand):
    help = 'Generates Google Meet links for consultations scheduled 24 hours from now'

    def handle(self, *args, **options):
        # Get consultations scheduled 24 hours from now
        target_time = timezone.now() + timedelta(hours=24)
        consultations = Consultation.objects.filter(
            date=target_time.date(),
            time__hour=target_time.hour,
            mode='virtual',
            meeting_link__isnull=True,
            status='confirmed'
        )

        for consultation in consultations:
            try:
                if consultation.generate_meeting_link():
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully generated meeting link for consultation {consultation.id}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Failed to generate meeting link for consultation {consultation.id}'
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error generating meeting link for consultation {consultation.id}: {str(e)}'
                    )
                ) 