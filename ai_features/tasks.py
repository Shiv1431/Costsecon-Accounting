from celery import shared_task
from django.contrib.auth.models import User
from core.models import Service, Consultation
from .services import (
    DocumentAnalyzer, ClientAnalyzer, ConsultationPredictor, MarketAnalyzer
)
from .models import (
    ClientBehaviorAnalysis, ServiceRecommendation, ConsultationPrediction,
    DocumentAnalysis, MarketTrendAnalysis
)

@shared_task
def analyze_client_behavior(user_id):
    try:
        user = User.objects.get(id=user_id)
        analyzer = ClientAnalyzer()
        analysis = analyzer.analyze_client_behavior(user)
        return f"Successfully analyzed behavior for user {user.username}"
    except Exception as e:
        return f"Error analyzing behavior for user {user_id}: {str(e)}"

@shared_task
def predict_consultation_metrics(consultation_id):
    try:
        consultation = Consultation.objects.get(id=consultation_id)
        predictor = ConsultationPredictor()
        prediction = predictor.predict_consultation_metrics(consultation)
        return f"Successfully predicted metrics for consultation {consultation_id}"
    except Exception as e:
        return f"Error predicting metrics for consultation {consultation_id}: {str(e)}"

@shared_task
def analyze_market_trends(service_id):
    try:
        service = Service.objects.get(id=service_id)
        analyzer = MarketAnalyzer()
        analysis = analyzer.analyze_market_trends(service)
        return f"Successfully analyzed market trends for service {service.name}"
    except Exception as e:
        return f"Error analyzing market trends for service {service_id}: {str(e)}"

@shared_task
def analyze_document(document_analysis_id):
    try:
        doc_analysis = DocumentAnalysis.objects.get(id=document_analysis_id)
        analyzer = DocumentAnalyzer()
        analysis = analyzer.analyze_document(doc_analysis.document, doc_analysis.document_type)
        doc_analysis.analysis_results = analysis
        doc_analysis.save()
        return f"Successfully analyzed document for user {doc_analysis.user.username}"
    except Exception as e:
        return f"Error analyzing document {document_analysis_id}: {str(e)}"

@shared_task
def update_all_predictions():
    """Update predictions for all active consultations"""
    active_statuses = ['pending', 'confirmed']
    consultations = Consultation.objects.filter(status__in=active_statuses)
    predictor = ConsultationPredictor()
    
    for consultation in consultations:
        try:
            predictor.predict_consultation_metrics(consultation)
        except Exception as e:
            print(f"Error updating prediction for consultation {consultation.id}: {str(e)}")
    
    return f"Updated predictions for {consultations.count()} consultations"

@shared_task
def analyze_all_clients():
    """Analyze behavior for all active clients"""
    users = User.objects.filter(is_active=True)
    analyzer = ClientAnalyzer()
    
    for user in users:
        try:
            analyzer.analyze_client_behavior(user)
        except Exception as e:
            print(f"Error analyzing behavior for user {user.username}: {str(e)}")
    
    return f"Analyzed behavior for {users.count()} users"

@shared_task
def update_market_analysis():
    """Update market analysis for all services"""
    services = Service.objects.all()
    analyzer = MarketAnalyzer()
    
    for service in services:
        try:
            analyzer.analyze_market_trends(service)
        except Exception as e:
            print(f"Error analyzing market trends for service {service.name}: {str(e)}")
    
    return f"Updated market analysis for {services.count()} services" 