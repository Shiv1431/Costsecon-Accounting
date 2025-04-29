import os
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import PyPDF2
import docx
import re
from datetime import datetime, timedelta
from django.conf import settings

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('vader_lexicon')

class DocumentAnalyzer:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        self.stop_words = set(stopwords.words('english'))

    def extract_text_from_file(self, file_path):
        """Extract text from different file types"""
        text = ""
        if file_path.endswith('.pdf'):
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        elif file_path.endswith(('.doc', '.docx')):
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        return text

    def analyze_document(self, file_path):
        """Analyze document content and extract key information"""
        text = self.extract_text_from_file(file_path)
        
        # Extract keywords
        words = word_tokenize(text.lower())
        keywords = [word for word in words if word.isalnum() and word not in self.stop_words]
        
        # Analyze sentiment
        sentiment = self.sia.polarity_scores(text)
        
        # Extract dates and numbers
        dates = re.findall(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text)
        numbers = re.findall(r'\b\d+\b', text)
        
        return {
            'keywords': list(set(keywords)),
            'sentiment': sentiment,
            'dates': dates,
            'numbers': numbers,
            'text_length': len(text)
        }

class ServiceRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')

    def get_recommendations(self, user_profile, consultation_history):
        """Generate personalized service recommendations"""
        # Combine user profile and history for analysis
        profile_text = f"{user_profile.business_type} {user_profile.industry} {user_profile.goals}"
        history_text = " ".join([f"{c.service.name} {c.notes}" for c in consultation_history])
        
        # Vectorize text
        text = f"{profile_text} {history_text}"
        tfidf_matrix = self.vectorizer.fit_transform([text])
        
        # Get all active services
        from .models import Service
        services = Service.objects.filter(is_active=True)
        service_descriptions = [s.description for s in services]
        
        # Calculate similarity
        service_matrix = self.vectorizer.transform(service_descriptions)
        similarities = cosine_similarity(tfidf_matrix, service_matrix)[0]
        
        # Get top recommendations
        top_indices = np.argsort(similarities)[-3:][::-1]
        recommendations = []
        
        for idx in top_indices:
            service = services[idx]
            recommendations.append({
                'service': service,
                'similarity_score': float(similarities[idx]),
                'reason': self._generate_recommendation_reason(service, text)
            })
        
        return recommendations

    def _generate_recommendation_reason(self, service, text):
        """Generate a human-readable reason for the recommendation"""
        keywords = set(service.description.lower().split())
        text_keywords = set(text.lower().split())
        common_keywords = keywords.intersection(text_keywords)
        
        if common_keywords:
            return f"Based on your interest in: {', '.join(common_keywords)}"
        return "Based on your profile and consultation history"

class ConsultationAnalyzer:
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()

    def analyze_consultation(self, consultation):
        """Analyze consultation details and generate insights"""
        # Combine all text fields for analysis
        text = f"{consultation.notes} {consultation.current_challenges} {consultation.goals}"
        
        # Analyze sentiment
        sentiment = self.sia.polarity_scores(text)
        
        # Determine priority based on sentiment and urgency
        priority = self._determine_priority(sentiment, consultation)
        
        # Extract keywords
        words = word_tokenize(text.lower())
        keywords = [word for word in words if word.isalnum() and word not in stopwords.words('english')]
        
        return {
            'sentiment': sentiment,
            'priority': priority,
            'keywords': list(set(keywords)),
            'analysis': self._generate_analysis(sentiment, priority, keywords)
        }

    def _determine_priority(self, sentiment, consultation):
        """Determine consultation priority based on sentiment and urgency"""
        if sentiment['compound'] < -0.5:
            return 'high'
        elif consultation.date - datetime.now().date() < timedelta(days=3):
            return 'high'
        elif sentiment['compound'] > 0.5:
            return 'low'
        return 'medium'

    def _generate_analysis(self, sentiment, priority, keywords):
        """Generate a human-readable analysis"""
        analysis = []
        
        if sentiment['compound'] < -0.5:
            analysis.append("The consultation shows signs of urgency and concern.")
        elif sentiment['compound'] > 0.5:
            analysis.append("The consultation has a positive tone.")
        
        if priority == 'high':
            analysis.append("This consultation requires immediate attention.")
        
        if keywords:
            analysis.append(f"Key topics: {', '.join(keywords[:5])}")
        
        return " ".join(analysis)

# Initialize analyzers
document_analyzer = DocumentAnalyzer()
service_recommender = ServiceRecommender()
consultation_analyzer = ConsultationAnalyzer() 