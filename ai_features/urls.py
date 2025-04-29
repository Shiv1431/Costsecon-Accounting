from django.urls import path
from . import views

app_name = 'ai_features'

urlpatterns = [
    path('financial-analysis/', views.financial_analysis, name='financial_analysis'),
    path('financial-analysis/<int:consultation_id>/', views.financial_analysis, name='financial_analysis_with_consultation'),
    path('document-classification/', views.document_classification, name='document_classification'),
    path('document-classification/<int:consultation_id>/', views.document_classification, name='document_classification_with_consultation'),
    path('smart-scheduling/', views.smart_scheduling, name='smart_scheduling'),
    path('track-behavior/<str:action_type>/', views.track_user_behavior, name='track_behavior'),
    path('track-behavior/<str:action_type>/<int:consultation_id>/', views.track_user_behavior, name='track_behavior_with_consultation'),
] 