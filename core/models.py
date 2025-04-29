from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import os

def document_upload_path(instance, filename):
    if isinstance(instance, Document):
        if instance.consultation and instance.consultation.id:
            return f'documents/{instance.consultation.id}/{filename}'
        elif instance.service and instance.service.id:
            return f'service_documents/{instance.service.id}/{filename}'
        return f'documents/temp/{filename}'
    elif isinstance(instance, Consultation):
        if instance.id:
            return f'consultation_documents/{instance.id}/{filename}'
        return f'consultation_documents/temp/{filename}'
    return f'documents/temp/{filename}'

class Contact(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"

class Service(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.IntegerField(help_text="Duration in minutes", default=60)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Consultation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    MODE_CHOICES = [
        ('in_person', 'In Person'),
        ('virtual', 'Virtual'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='virtual')
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    meeting_link = models.URLField(blank=True, null=True)
    meeting_link_sent = models.BooleanField(default=False)
    consultant = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='consultations_as_consultant')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Service-specific fields
    tax_year = models.CharField(max_length=9, null=True, blank=True)
    financial_year = models.CharField(max_length=9, null=True, blank=True)
    company_name = models.CharField(max_length=200, null=True, blank=True)
    gst_number = models.CharField(max_length=15, null=True, blank=True)
    pan_number = models.CharField(max_length=10, null=True, blank=True)
    business_type = models.CharField(max_length=100, null=True, blank=True)
    number_of_employees = models.IntegerField(null=True, blank=True)
    consultation_type = models.CharField(max_length=100, null=True, blank=True)
    current_challenges = models.TextField(null=True, blank=True)
    goals = models.TextField(null=True, blank=True)

    # Document fields
    supporting_documents = models.FileField(upload_to=document_upload_path, null=True, blank=True)
    additional_documents = models.FileField(upload_to=document_upload_path, null=True, blank=True)

    # AI-related fields
    ai_recommendations = models.JSONField(null=True, blank=True)
    ai_analysis = models.TextField(null=True, blank=True)
    ai_sentiment = models.CharField(max_length=20, null=True, blank=True)
    ai_priority = models.CharField(max_length=20, null=True, blank=True)
    ai_keywords = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.service.name} - {self.date}"

class AIAnalysis(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='ai_analyses')
    analysis_type = models.CharField(max_length=50)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.consultation} - {self.analysis_type}"

class Feedback(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    consultant_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], null=True, blank=True)
    service_comment = models.TextField(blank=True)
    consultant_comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.consultation} by {self.user.username}"

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('supporting', 'Supporting Document'),
        ('additional', 'Additional Document'),
        ('report', 'Report'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='documents/')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, default='other')
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=True, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_private = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super().delete(*args, **kwargs)
