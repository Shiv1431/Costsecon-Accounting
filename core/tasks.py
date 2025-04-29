from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from .models import Consultation
import random
import string
from django.conf import settings

@shared_task
def send_meeting_links():
    tomorrow = timezone.now().date() + timedelta(days=1)
    consultations = Consultation.objects.filter(
        date=tomorrow,
        mode='virtual',
        status='confirmed',
        meeting_link_sent=False
    )
    
    for consultation in consultations:
        if not consultation.meeting_link:
            consultation.generate_meeting_link()
        consultation.send_meeting_link()

@shared_task
def analyze_consultation_patterns():
    # This task will analyze consultation patterns and generate insights
    # Implementation will be added later
    pass

@shared_task
def analyze_consultation_patterns():
    # Get all consultations
    consultations = Consultation.objects.all()
    
    # Analyze patterns (this is a simple example, you can add more complex analysis)
    service_popularity = {}
    time_preferences = {}
    mode_preferences = {}
    
    for consultation in consultations:
        # Service popularity
        service_name = consultation.service.name
        service_popularity[service_name] = service_popularity.get(service_name, 0) + 1
        
        # Time preferences
        hour = consultation.time.hour
        time_preferences[hour] = time_preferences.get(hour, 0) + 1
        
        # Mode preferences
        mode = consultation.mode
        mode_preferences[mode] = mode_preferences.get(mode, 0) + 1
    
    # Save analysis results (you can create a model for this)
    print("Service Popularity:", service_popularity)
    print("Time Preferences:", time_preferences)
    print("Mode Preferences:", mode_preferences)
    
    # You can add more analysis here, such as:
    # - Peak booking times
    # - Most common consultation durations
    # - User demographics
    # - Seasonal trends
    # - Revenue analysis 