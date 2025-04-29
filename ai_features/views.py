from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import FinancialAnalysis, DocumentClassification, UserBehavior
from core.models import Consultation
import json
from datetime import datetime
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import os
from django.conf import settings

# Create your views here.

@login_required
def financial_analysis(request, consultation_id=None):
    if request.method == 'POST':
        data = json.loads(request.body)
        analysis_type = data.get('analysis_type')
        
        # Sample ML prediction (replace with actual model)
        if analysis_type == 'TAX_OPTIMIZATION':
            # Simulate tax optimization prediction
            predictions = {
                'suggested_deductions': np.random.randint(1000, 5000),
                'estimated_tax_savings': np.random.randint(500, 2000),
                'recommended_strategies': ['Maximize retirement contributions', 'Consider HSA contributions']
            }
        elif analysis_type == 'INVESTMENT':
            # Simulate investment analysis
            predictions = {
                'risk_score': np.random.uniform(0.3, 0.8),
                'recommended_portfolio': {
                    'stocks': np.random.randint(40, 70),
                    'bonds': np.random.randint(20, 40),
                    'cash': np.random.randint(5, 15)
                }
            }
        else:
            predictions = {'error': 'Invalid analysis type'}

        analysis = FinancialAnalysis.objects.create(
            user=request.user,
            consultation_id=consultation_id,
            analysis_type=analysis_type,
            data=data,
            predictions=predictions
        )
        
        return JsonResponse({'status': 'success', 'analysis_id': analysis.id})
    
    return render(request, 'ai_features/financial_analysis.html')

@login_required
def document_classification(request, consultation_id=None):
    if request.method == 'POST' and request.FILES.get('document'):
        document = request.FILES['document']
        
        # Sample document classification (replace with actual model)
        document_types = ['TAX_FORM', 'INVOICE', 'RECEIPT', 'CONTRACT', 'OTHER']
        predicted_type = np.random.choice(document_types)
        confidence = np.random.uniform(0.7, 0.95)
        
        classification = DocumentClassification.objects.create(
            user=request.user,
            consultation_id=consultation_id,
            document=document,
            document_type=predicted_type,
            confidence_score=confidence
        )
        
        return JsonResponse({
            'status': 'success',
            'document_type': predicted_type,
            'confidence': confidence
        })
    
    return render(request, 'ai_features/document_classification.html')

@login_required
def smart_scheduling(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        consultation_id = data.get('consultation_id')
        
        # Analyze user behavior for smart scheduling
        user_actions = UserBehavior.objects.filter(user=request.user)
        preferred_times = []
        
        for action in user_actions:
            if action.metadata and 'preferred_time' in action.metadata:
                preferred_times.append(action.metadata['preferred_time'])
        
        # Simple recommendation based on user history
        if preferred_times:
            recommended_time = max(set(preferred_times), key=preferred_times.count)
        else:
            recommended_time = '10:00 AM'  # Default time
        
        return JsonResponse({
            'status': 'success',
            'recommended_time': recommended_time
        })
    
    return render(request, 'ai_features/smart_scheduling.html')

def track_user_behavior(request, action_type, consultation_id=None, metadata=None):
    if request.user.is_authenticated:
        UserBehavior.objects.create(
            user=request.user,
            consultation_id=consultation_id,
            action_type=action_type,
            metadata=metadata or {}
        )
    return JsonResponse({'status': 'success'})
