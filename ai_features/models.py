from django.db import models
from django.contrib.auth.models import User
from core.models import Service, Consultation

class FinancialAnalysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, null=True, blank=True)
    analysis_type = models.CharField(max_length=50, choices=[
        ('TAX_OPTIMIZATION', 'Tax Optimization'),
        ('INVESTMENT', 'Investment Analysis'),
        ('BUDGET', 'Budget Planning'),
    ])
    data = models.JSONField()
    predictions = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s {self.analysis_type} Analysis"

class DocumentClassification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, null=True, blank=True)
    document = models.FileField(upload_to='documents/')
    document_type = models.CharField(max_length=50, choices=[
        ('TAX_FORM', 'Tax Form'),
        ('INVOICE', 'Invoice'),
        ('RECEIPT', 'Receipt'),
        ('CONTRACT', 'Contract'),
        ('OTHER', 'Other'),
    ])
    confidence_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s {self.document_type} Document"

class UserBehavior(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, null=True, blank=True)
    action_type = models.CharField(max_length=50, choices=[
        ('VIEW', 'View'),
        ('BOOK', 'Book'),
        ('CANCEL', 'Cancel'),
        ('RESCHEDULE', 'Reschedule'),
    ])
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField()

    def __str__(self):
        return f"{self.user.username}'s {self.action_type} Action"

class ClientBehaviorAnalysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service_preferences = models.JSONField(default=dict)
    interaction_patterns = models.JSONField(default=dict)
    predicted_next_service = models.ForeignKey(Service, null=True, blank=True, on_delete=models.SET_NULL)
    last_analyzed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analysis for {self.user.username}"

class ServiceRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recommended_services = models.ManyToManyField(Service)
    confidence_scores = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recommendations for {self.user.username}"

class ConsultationPrediction(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    predicted_duration = models.IntegerField(help_text="Predicted duration in minutes")
    predicted_complexity = models.FloatField(help_text="Predicted complexity score (0-1)")
    predicted_success_rate = models.FloatField(help_text="Predicted success rate (0-1)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prediction for consultation {self.consultation.id}"

class DocumentAnalysis(models.Model):
    DOCUMENT_TYPES = [
        ('tax_return', 'Tax Return'),
        ('financial_statement', 'Financial Statement'),
        ('invoice', 'Invoice'),
        ('receipt', 'Receipt'),
        ('other', 'Other')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document = models.FileField(upload_to='analyzed_documents/')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    extracted_text = models.TextField()
    analysis_results = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document_type} analysis for {self.user.username}"

class MarketTrendAnalysis(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    trend_data = models.JSONField(default=dict)
    predicted_demand = models.FloatField()
    seasonal_patterns = models.JSONField(default=dict)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Market analysis for {self.service.name}"
