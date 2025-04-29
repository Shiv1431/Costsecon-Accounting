import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import pandas as pd
from datetime import datetime, timedelta
import joblib
import os
from django.conf import settings
from .models import (
    ClientBehaviorAnalysis, ServiceRecommendation, ConsultationPrediction,
    DocumentAnalysis, MarketTrendAnalysis
)
from core.models import Service, Consultation
import PyPDF2
import docx
import re
from textblob import TextBlob

class DocumentAnalyzer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        
    def extract_text(self, document):
        text = ""
        if document.name.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(document)
            for page in pdf_reader.pages:
                text += page.extract_text()
        elif document.name.endswith(('.doc', '.docx')):
            doc = docx.Document(document)
            for para in doc.paragraphs:
                text += para.text + '\n'
        return text
    
    def analyze_document(self, document, document_type):
        text = self.extract_text(document)
        analysis = {
            'word_count': len(text.split()),
            'sentiment': self._analyze_sentiment(text),
            'key_entities': self._extract_entities(text),
            'document_type_confidence': self._predict_document_type(text),
            'summary': self._generate_summary(text)
        }
        return analysis
    
    def _analyze_sentiment(self, text):
        blob = TextBlob(text)
        return {
            'polarity': blob.sentiment.polarity,
            'subjectivity': blob.sentiment.subjectivity
        }
    
    def _extract_entities(self, text):
        # Add your entity extraction logic here
        return []
    
    def _predict_document_type(self, text):
        # Add document type prediction logic
        return 0.95
    
    def _generate_summary(self, text):
        # Add text summarization logic
        return text[:500] + "..."

class ClientAnalyzer:
    def __init__(self):
        self.model_path = os.path.join(settings.AI_MODELS_DIR, 'client_behavior.joblib')
        
    def analyze_client_behavior(self, user):
        consultations = Consultation.objects.filter(user=user)
        
        if not consultations.exists():
            return None
            
        # Analyze service preferences
        service_preferences = self._analyze_service_preferences(consultations)
        
        # Analyze interaction patterns
        interaction_patterns = self._analyze_interaction_patterns(consultations)
        
        # Predict next service
        predicted_service = self._predict_next_service(user, service_preferences)
        
        # Save analysis
        analysis, _ = ClientBehaviorAnalysis.objects.update_or_create(
            user=user,
            defaults={
                'service_preferences': service_preferences,
                'interaction_patterns': interaction_patterns,
                'predicted_next_service': predicted_service
            }
        )
        
        return analysis
    
    def _analyze_service_preferences(self, consultations):
        preferences = {}
        for consultation in consultations:
            service_name = consultation.service.name
            if service_name in preferences:
                preferences[service_name] += 1
            else:
                preferences[service_name] = 1
        return preferences
    
    def _analyze_interaction_patterns(self, consultations):
        patterns = {
            'preferred_time': self._get_preferred_time(consultations),
            'preferred_mode': self._get_preferred_mode(consultations),
            'consultation_frequency': self._get_consultation_frequency(consultations)
        }
        return patterns
    
    def _predict_next_service(self, user, preferences):
        if not preferences:
            return None
            
        # Get most used service
        most_used = max(preferences.items(), key=lambda x: x[1])[0]
        return Service.objects.filter(name=most_used).first()
    
    def _get_preferred_time(self, consultations):
        times = [c.time for c in consultations]
        if times:
            return times[0].strftime('%H:%M')
        return None
    
    def _get_preferred_mode(self, consultations):
        modes = [c.mode for c in consultations]
        if modes:
            return max(set(modes), key=modes.count)
        return None
    
    def _get_consultation_frequency(self, consultations):
        if len(consultations) < 2:
            return "Irregular"
            
        dates = [c.date for c in consultations]
        avg_days = sum((dates[i+1] - dates[i]).days for i in range(len(dates)-1)) / (len(dates)-1)
        
        if avg_days <= 7:
            return "Weekly"
        elif avg_days <= 30:
            return "Monthly"
        else:
            return "Irregular"

class ConsultationPredictor:
    def __init__(self):
        self.model_path = os.path.join(settings.AI_MODELS_DIR, 'consultation_predictor.joblib')
        
    def predict_consultation_metrics(self, consultation):
        # Extract features
        features = self._extract_features(consultation)
        
        # Make predictions
        duration = self._predict_duration(features)
        complexity = self._predict_complexity(features)
        success_rate = self._predict_success_rate(features)
        
        # Save predictions
        prediction, _ = ConsultationPrediction.objects.update_or_create(
            consultation=consultation,
            defaults={
                'predicted_duration': duration,
                'predicted_complexity': complexity,
                'predicted_success_rate': success_rate
            }
        )
        
        return prediction
    
    def _extract_features(self, consultation):
        features = {
            'service_type': consultation.service.name,
            'mode': consultation.mode,
            'time_of_day': consultation.time.hour,
            'day_of_week': consultation.date.weekday(),
            'client_history': len(Consultation.objects.filter(user=consultation.user))
        }
        return features
    
    def _predict_duration(self, features):
        # Add duration prediction logic
        return 60
    
    def _predict_complexity(self, features):
        # Add complexity prediction logic
        return 0.7
    
    def _predict_success_rate(self, features):
        # Add success rate prediction logic
        return 0.85

class MarketAnalyzer:
    def __init__(self):
        self.model_path = os.path.join(settings.AI_MODELS_DIR, 'market_analyzer.joblib')
        
    def analyze_market_trends(self, service):
        # Collect historical data
        consultations = Consultation.objects.filter(service=service)
        
        if not consultations.exists():
            return None
            
        # Analyze trends
        trend_data = self._analyze_trends(consultations)
        
        # Predict demand
        predicted_demand = self._predict_demand(trend_data)
        
        # Analyze seasonal patterns
        seasonal_patterns = self._analyze_seasonal_patterns(consultations)
        
        # Save analysis
        analysis, _ = MarketTrendAnalysis.objects.update_or_create(
            service=service,
            defaults={
                'trend_data': trend_data,
                'predicted_demand': predicted_demand,
                'seasonal_patterns': seasonal_patterns
            }
        )
        
        return analysis
    
    def _analyze_trends(self, consultations):
        monthly_counts = {}
        for consultation in consultations:
            month_key = consultation.date.strftime('%Y-%m')
            if month_key in monthly_counts:
                monthly_counts[month_key] += 1
            else:
                monthly_counts[month_key] = 1
        return monthly_counts
    
    def _predict_demand(self, trend_data):
        # Add demand prediction logic
        return 0.8
    
    def _analyze_seasonal_patterns(self, consultations):
        patterns = {
            'weekday_distribution': self._get_weekday_distribution(consultations),
            'monthly_distribution': self._get_monthly_distribution(consultations),
            'time_distribution': self._get_time_distribution(consultations)
        }
        return patterns
    
    def _get_weekday_distribution(self, consultations):
        distribution = {i: 0 for i in range(7)}
        for consultation in consultations:
            distribution[consultation.date.weekday()] += 1
        return distribution
    
    def _get_monthly_distribution(self, consultations):
        distribution = {i: 0 for i in range(1, 13)}
        for consultation in consultations:
            distribution[consultation.date.month] += 1
        return distribution
    
    def _get_time_distribution(self, consultations):
        distribution = {i: 0 for i in range(24)}
        for consultation in consultations:
            distribution[consultation.time.hour] += 1
        return distribution 