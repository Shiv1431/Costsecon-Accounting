from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
from .models import Service, Consultation, Feedback, Contact, Document, AIAnalysis
from accounts.models import UserProfile
from .forms import ConsultationForm, FeedbackForm, ServiceFilterForm, ContactForm, DocumentForm
import random
import string
import paypalrestsdk
import time
from django.urls import reverse
import razorpay
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from datetime import datetime, timedelta
import joblib
import os
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import PyPDF2
import docx
import re
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db.models import Sum, Avg
from django.contrib.auth.models import User
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import DetailView
from .ai_utils import document_analyzer, service_recommender, consultation_analyzer

logger = logging.getLogger(__name__)

# Initialize Razorpay client
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

# AI/ML Models
class ServiceRecommender:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServiceRecommender, cls).__new__(cls)
            cls._instance.service_indices = {}
        return cls._instance

    def initialize_service_indices(self):
        try:
            services = Service.objects.all()
            for idx, service in enumerate(services):
                self.service_indices[service.id] = idx
        except:
            # Handle case when database table doesn't exist yet
            pass
    
    def recommend_services(self, service_id, num_recommendations=3):
        if not self.service_indices:
            self.initialize_service_indices()
        
        if service_id not in self.service_indices:
            return Service.objects.none()
            
        # Get all services except the current one
        services = Service.objects.exclude(id=service_id)
        return services.order_by('?')[:num_recommendations]

class ConsultationAnalyzer:
    def __init__(self):
        self.model_path = os.path.join(settings.BASE_DIR, 'ai_models', 'consultation_analyzer.joblib')
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
        else:
            self.model = None
    
    def predict_consultation_duration(self, service_type, mode):
        if self.model:
            features = pd.DataFrame({
                'service_type': [service_type],
                'mode': [mode]
            })
            return self.model.predict(features)[0]
        return 60  # Default duration in minutes

# Initialize AI/ML components
consultation_analyzer = ConsultationAnalyzer()

def get_service_recommender():
    return ServiceRecommender()

# Services data
SERVICES = [
    {
        'id': 1,
        'name': 'Personalized Tax Solutions',
        'description': 'Expert tax planning and preparation services tailored to your individual needs. We help you maximize deductions and ensure compliance with tax regulations.',
        'price': 2999.00,
        'duration': 60,
        'fields': ['tax_year', 'income_sources', 'previous_returns', 'deduction_documents']
    },
    {
        'id': 2,
        'name': 'Comprehensive Financial Preparation',
        'description': 'Complete financial statement preparation and analysis. We help you understand your financial position and make informed decisions.',
        'price': 3999.00,
        'duration': 90,
        'fields': ['financial_year', 'financial_statements', 'bank_statements', 'investment_details']
    },
    {
        'id': 3,
        'name': 'Strategic Corporate Tax Management',
        'description': 'Professional corporate tax planning and compliance services. We help businesses optimize their tax strategy and maintain regulatory compliance.',
        'price': 4999.00,
        'duration': 120,
        'fields': ['company_name', 'gst_number', 'pan_number', 'financial_statements']
    },
    {
        'id': 4,
        'name': 'Precise Bookkeeping Solutions',
        'description': 'Accurate and efficient bookkeeping services. We maintain your financial records and provide regular reports to help you track your business performance.',
        'price': 1999.00,
        'duration': 60,
        'fields': ['accounting_software', 'bank_statements', 'invoices', 'expense_receipts']
    },
    {
        'id': 5,
        'name': 'Efficient GST Return Services',
        'description': 'Timely and accurate GST return filing services. We ensure compliance with GST regulations and help you avoid penalties.',
        'price': 2499.00,
        'duration': 45,
        'fields': ['gst_number', 'financial_year', 'sales_invoices', 'purchase_invoices']
    },
    {
        'id': 6,
        'name': 'Strategic Business Consultation',
        'description': 'Expert business advisory services. We help you develop strategies for growth, improve operations, and achieve your business goals.',
        'price': 3499.00,
        'duration': 90,
        'fields': ['business_type', 'business_plan', 'financial_statements']
    },
    {
        'id': 7,
        'name': 'Effortless Payroll Management',
        'description': 'Comprehensive payroll processing and management services. We handle all aspects of payroll, from calculations to tax deductions.',
        'price': 1799.00,
        'duration': 45,
        'fields': ['number_of_employees', 'salary_structure', 'attendance_records', 'pf_esi_details']
    },
    {
        'id': 8,
        'name': 'Streamlined Online Filing',
        'description': 'Efficient online document filing and management services. We help you organize and maintain your digital records securely.',
        'price': 1499.00,
        'duration': 30,
        'fields': ['filing_type', 'financial_year', 'supporting_documents']
    },
    {
        'id': 9,
        'name': 'Personalized Consultation',
        'description': 'One-on-one consultation services tailored to your specific needs. Get expert advice on your financial and accounting concerns.',
        'price': 1999.00,
        'duration': 60,
        'fields': ['consultation_type', 'current_challenges', 'goals']
    }
]

def home(request):
    services = Service.objects.all()
    return render(request, 'core/home.html', {'services': services})

def about(request):
    return render(request, 'core/about.html')

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            
            try:
                # Send email to admin
                admin_subject = f'New Contact Form Submission - {contact.subject}'
                admin_html_message = render_to_string('emails/admin_contact_notification.html', {
                    'name': contact.name,
                    'email': contact.email,
                    'subject': contact.subject,
                    'message': contact.message,
                    'created_at': contact.created_at,
                })
                admin_plain_message = strip_tags(admin_html_message)
                
                send_mail(
                    admin_subject,
                    admin_plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                    html_message=admin_html_message,
                    fail_silently=False
                )
                
                # Send acknowledgment email to client
                client_subject = 'Thank you for contacting Costsecon Accounting Inc'
                client_html_message = render_to_string('emails/contact_acknowledgment.html', {
                    'name': contact.name,
                    'subject': contact.subject,
                    'message': contact.message,
                })
                client_plain_message = strip_tags(client_html_message)
                
                send_mail(
                    client_subject,
                    client_plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [contact.email],
                    html_message=client_html_message,
                    fail_silently=False
                )
                
                messages.success(request, 'Thank you for contacting us! We have received your message and will get back to you soon.')
                return redirect('core:contact')
                
            except Exception as e:
                logger.error(f"Failed to send contact form emails: {str(e)}")
                messages.error(request, 'There was an error sending your message. Please try again later.')
                return redirect('core:contact')
    else:
        form = ContactForm()
    
    return render(request, 'core/contact.html', {'form': form})

def service_list(request):
    services = Service.objects.all()
    return render(request, 'core/service_list.html', {'services': services})

class ServiceDetailView(LoginRequiredMixin, DetailView):
    model = Service
    template_name = 'core/service_detail.html'
    context_object_name = 'service'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['document_form'] = DocumentForm()
        
        # Get documents based on user permissions
        if self.request.user.is_staff:
            context['documents'] = self.object.documents.all()
        else:
            context['documents'] = self.object.documents.filter(is_private=False)
        
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = DocumentForm(request.POST, request.FILES)
        
        if form.is_valid():
            document = form.save(commit=False)
            document.service = self.object
            document.uploaded_by = request.user
            document.save()
            return redirect('service_detail', pk=self.object.pk)
        
        context = self.get_context_data()
        context['document_form'] = form
        return self.render_to_response(context)

@login_required
def book_consultation(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    
    if request.method == 'POST':
        form = ConsultationForm(request.POST, request.FILES)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.user = request.user
            consultation.service = service
            consultation.status = 'pending'
            consultation.payment_amount = service.price
            
            # Handle document uploads
            if 'supporting_documents' in request.FILES:
                consultation.supporting_documents = request.FILES['supporting_documents']
            if 'additional_documents' in request.FILES:
                consultation.additional_documents = request.FILES['additional_documents']
            
            consultation.save()
            
            # Analyze documents if uploaded
            if consultation.supporting_documents:
                try:
                    analysis = document_analyzer.analyze_document(consultation.supporting_documents.path)
                    consultation.ai_keywords = analysis['keywords']
                    consultation.ai_sentiment = 'positive' if analysis['sentiment']['compound'] > 0 else 'negative'
                    consultation.save()
                    
                    # Create AI analysis record
                    AIAnalysis.objects.create(
                        consultation=consultation,
                        analysis_type='document',
                        content=json.dumps(analysis),
                        metadata={'file_type': consultation.supporting_documents.name.split('.')[-1]}
                    )
                except Exception as e:
                    logger.error(f"Error analyzing document: {str(e)}")
            
            # Analyze consultation details
            try:
                consultation_analysis = consultation_analyzer.analyze_consultation(consultation)
                consultation.ai_analysis = consultation_analysis['analysis']
                consultation.ai_priority = consultation_analysis['priority']
                consultation.save()
                
                # Create AI analysis record
                AIAnalysis.objects.create(
                    consultation=consultation,
                    analysis_type='consultation',
                    content=consultation_analysis['analysis'],
                    metadata={'priority': consultation_analysis['priority']}
                )
            except Exception as e:
                logger.error(f"Error analyzing consultation: {str(e)}")
            
            # Send notification to admin
            try:
                send_mail(
                    'New Consultation Booking',
                    f'A new consultation has been booked by {consultation.user.get_full_name()}',
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                    fail_silently=False,
                )
            except Exception as e:
                logger.error(f"Error sending email: {str(e)}")
            
            return redirect('core:payment', consultation_id=consultation.id)
    else:
        form = ConsultationForm()
    
    return render(request, 'core/book_consultation.html', {
        'form': form,
        'service': service
    })

@login_required
def payment(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id, user=request.user)
    
    if consultation.status != 'pending':
        messages.warning(request, 'This consultation is not pending payment.')
        return redirect('core:profile')
    
    # Ensure payment_amount is set
    if not consultation.payment_amount:
        consultation.payment_amount = consultation.service.price
        consultation.save()
    
    # Convert amount to paise (multiply by 100)
    amount = int(float(consultation.payment_amount) * 100)
    currency = 'INR'
    
    # Check if Razorpay key is configured
    if not settings.RAZORPAY_KEY_ID:
        messages.error(request, 'Payment system is not configured. Please contact support.')
        return redirect('core:profile')
    
    order_data = {
        'amount': amount,
        'currency': currency,
        'payment_capture': 1,
        'notes': {
            'consultation_id': consultation_id,
            'user_id': request.user.id
        }
    }
    
    try:
        order = razorpay_client.order.create(data=order_data)
        return render(request, 'core/payment.html', {
            'consultation': consultation,
            'order_id': order['id'],
            'amount': amount,
            'currency': currency,
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'user': request.user
        })
    except Exception as e:
        messages.error(request, 'Unable to process payment. Please try again later.')
        return redirect('core:profile')

@login_required
def verify_payment(request, consultation_id):
    if request.method == 'POST':
        try:
            consultation = get_object_or_404(Consultation, id=consultation_id, user=request.user)
            
            # Get payment details from request
            payment_id = request.POST.get('razorpay_payment_id')
            order_id = request.POST.get('razorpay_order_id')
            signature = request.POST.get('razorpay_signature')
            
            if not all([payment_id, order_id, signature]):
                messages.error(request, 'Missing payment details')
                return redirect('core:payment', consultation_id=consultation_id)
            
            # Verify payment with Razorpay
            params_dict = {
                'razorpay_payment_id': payment_id,
                'razorpay_order_id': order_id,
                'razorpay_signature': signature
            }
            
            try:
                razorpay_client.utility.verify_payment_signature(params_dict)
                
                # Update consultation status
                consultation.payment_status = True
                consultation.status = 'confirmed'
                consultation.save()
                
                # Send confirmation emails
                try:
                    # Send to user
                    user_subject = 'Payment Confirmation - Costsecon Accounting Inc'
                    user_message = f'''
                    Dear {consultation.user.get_full_name()},
                    
                    Your payment has been successfully processed for the following consultation:
                    
                    Service: {consultation.service.name}
                    Date: {consultation.date}
                    Time: {consultation.time}
                    Amount: ₹{consultation.payment_amount}
                    
                    Thank you for choosing Costsecon Accounting Inc.
                    '''
                    
                    send_mail(
                        user_subject,
                        user_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [consultation.user.email],
                        fail_silently=False,
                    )
                    
                    # Send to admin
                    admin_subject = f'New Payment Received - {consultation.user.get_full_name()}'
                    admin_message = f'''
                    A new payment has been received:
                    
                    Client: {consultation.user.get_full_name()}
                    Service: {consultation.service.name}
                    Amount: ₹{consultation.payment_amount}
                    Date: {consultation.date}
                    Time: {consultation.time}
                    '''
                    
                    send_mail(
                        admin_subject,
                        admin_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [settings.ADMIN_EMAIL],
                        fail_silently=False,
                    )
                except Exception as e:
                    logger.error(f"Error sending confirmation emails: {str(e)}")
                
                messages.success(request, 'Payment successful! Your consultation has been confirmed.')
                return redirect('core:consultation_detail', consultation_id=consultation.id)
                
            except razorpay.errors.SignatureVerificationError:
                messages.error(request, 'Payment verification failed. Please try again.')
                return redirect('core:payment', consultation_id=consultation_id)
                
        except Exception as e:
            logger.error(f"Error processing payment: {str(e)}")
            messages.error(request, 'An error occurred while processing your payment. Please try again.')
            return redirect('core:payment', consultation_id=consultation_id)
    
    return redirect('core:payment', consultation_id=consultation_id)

@login_required
def submit_feedback(request, consultation_id):
    consultation = get_object_or_404(Consultation, pk=consultation_id, user=request.user)
    
    # Check if feedback already exists
    if hasattr(consultation, 'feedback'):
        messages.warning(request, 'You have already submitted feedback for this consultation.')
        return redirect('core:my_consultations')
    
    if request.method == 'POST':
        form = FeedbackForm(request.POST, consultation=consultation)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.consultation = consultation
            feedback.user = request.user
            
            # Handle star ratings
            feedback.service_rating = int(request.POST.get('service_rating', 0))
            if consultation.consultant:
                feedback.consultant_rating = int(request.POST.get('consultant_rating', 0))
            
            feedback.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('core:my_consultations')
    else:
        form = FeedbackForm(consultation=consultation)
    
    return render(request, 'core/submit_feedback.html', {
        'form': form,
        'consultation': consultation
    })

@login_required
def consultation_detail(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id, user=request.user)
    
    # Get all documents associated with this consultation
    documents = consultation.documents.all().order_by('-created_at')
    
    # Get feedback if exists
    feedback = getattr(consultation, 'feedback', None)
    
    # Get service-specific information
    service_info = {}
    if consultation.tax_year:
        service_info['tax_year'] = consultation.tax_year
    if consultation.financial_year:
        service_info['financial_year'] = consultation.financial_year
    if consultation.company_name:
        service_info['company_name'] = consultation.company_name
    if consultation.gst_number:
        service_info['gst_number'] = consultation.gst_number
    if consultation.pan_number:
        service_info['pan_number'] = consultation.pan_number
    
    context = {
        'consultation': consultation,
        'documents': documents,
        'feedback': feedback,
        'service_info': service_info,
    }
    
    return render(request, 'core/consultation_detail.html', context)

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('core:home')
    return redirect('core:profile')

@login_required
def profile(request):
    if request.user.userprofile.is_consultant:
        return redirect('core:consultant_dashboard')
    
    # Get client's consultations
    consultations = Consultation.objects.filter(user=request.user).order_by('-date', '-time')
    upcoming_consultations = consultations.filter(date__gte=timezone.now().date(), status='confirmed')
    pending_consultations = consultations.filter(status='pending')
    completed_consultations = consultations.filter(status='completed')
    
    # Get client's documents
    documents = Document.objects.filter(consultation__user=request.user).order_by('-uploaded_at')
    
    context = {
        'upcoming_consultations': upcoming_consultations,
        'pending_consultations': pending_consultations,
        'completed_consultations': completed_consultations,
        'upcoming_consultations_count': upcoming_consultations.count(),
        'pending_consultations_count': pending_consultations.count(),
        'completed_consultations_count': completed_consultations.count(),
        'total_documents_count': documents.count(),
        'recent_documents': documents[:5],
    }
    
    return render(request, 'core/client_dashboard.html', context)

@login_required
def client_dashboard(request):
    # Get user's consultations
    consultations = Consultation.objects.filter(user=request.user).order_by('-date', '-time')
    
    # Get AI recommendations
    try:
        recommendations = service_recommender.get_recommendations(
            request.user.userprofile,
            consultations
        )
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        recommendations = []
    
    # Get recent AI analyses
    recent_analyses = AIAnalysis.objects.filter(
        consultation__user=request.user
    ).order_by('-created_at')[:5]
    
    return render(request, 'core/client_dashboard.html', {
        'consultations': consultations,
        'recommendations': recommendations,
        'recent_analyses': recent_analyses
    })

@login_required
def consultant_dashboard(request):
    if not request.user.userprofile.is_consultant:
        return redirect('core:client_dashboard')
    
    # Get assigned consultations
    consultations = Consultation.objects.filter(
        consultant=request.user,
        status__in=['confirmed', 'pending']
    ).order_by('-date', '-time')
    
    # Get high priority consultations
    high_priority = consultations.filter(ai_priority='high')
    
    # Get recent document analyses
    recent_analyses = AIAnalysis.objects.filter(
        consultation__consultant=request.user,
        analysis_type='document'
    ).order_by('-created_at')[:5]
    
    return render(request, 'core/consultant_dashboard.html', {
        'consultations': consultations,
        'high_priority': high_priority,
        'recent_analyses': recent_analyses
    })

@login_required
def client_detail(request, client_id):
    if not request.user.userprofile.is_consultant:
        return redirect('core:client_dashboard')
    
    client = get_object_or_404(User, id=client_id)
    consultations = Consultation.objects.filter(user=client, consultant=request.user.userprofile.consultant)
    
    context = {
        'client': client,
        'consultations': consultations,
    }
    
    return render(request, 'core/client_detail.html', context)

@login_required
def update_profile(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            first_name, *last_name = name.split(' ', 1)
            request.user.first_name = first_name
            request.user.last_name = last_name[0] if last_name else ''
            request.user.save()
            messages.success(request, 'Profile updated successfully!')
        else:
            messages.error(request, 'Name is required.')
    return redirect('core:profile')

def is_admin(user):
    try:
        return user.userprofile.is_admin
    except UserProfile.DoesNotExist:
        return False

@user_passes_test(is_admin)
def admin_dashboard(request):
    form = ServiceFilterForm(request.GET)
    consultations = Consultation.objects.all().order_by('date', 'time')
    
    if form.is_valid():
        if form.cleaned_data['date_from']:
            consultations = consultations.filter(date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data['date_to']:
            consultations = consultations.filter(date__lte=form.cleaned_data['date_to'])
        if form.cleaned_data['mode']:
            consultations = consultations.filter(mode=form.cleaned_data['mode'])
        if form.cleaned_data['service']:
            consultations = consultations.filter(service=form.cleaned_data['service'])
    
    return render(request, 'core/admin_dashboard.html', {
        'consultations': consultations,
        'filter_form': form
    })

@user_passes_test(is_admin)
def generate_meeting_link(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)
    if consultation.mode == 'virtual' and not consultation.meeting_link:
        # Generate a random meeting ID
        meeting_id = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        meeting_link = f"https://meet.google.com/{meeting_id}"
        consultation.meeting_link = meeting_link
        consultation.save()
        
        # Send email to client
        send_mail(
            'Virtual Consultation Link',
            f'Your virtual consultation link: {meeting_link}',
            settings.DEFAULT_FROM_EMAIL,
            [consultation.client.email],
            fail_silently=False,
        )
        
        messages.success(request, 'Meeting link generated and sent to client.')
    return redirect('admin_dashboard')

@login_required
def create_order(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id, user=request.user)
    
    if consultation.status != 'pending':
        return JsonResponse({'error': 'Invalid consultation status'}, status=400)
    
    amount = int(consultation.service.price * 100)  # Convert to paise
    order_data = {
        'amount': amount,
        'currency': 'INR',
        'payment_capture': 1
    }
    
    try:
        order = razorpay_client.order.create(data=order_data)
        return JsonResponse({
            'id': order['id'],
            'amount': amount,
            'currency': 'INR'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def my_consultations(request):
    consultations = Consultation.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/my_consultations.html', {'consultations': consultations})

@require_POST
@login_required
def analyze_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    
    if not request.user.is_staff and document.uploaded_by != request.user:
        messages.error(request, "You don't have permission to analyze this document.")
        return redirect('core:consultation_detail', consultation_id=document.consultation.id)
    
    try:
        analysis = document_analyzer.analyze_document(document.file.path)
        
        # Create AI analysis record
        AIAnalysis.objects.create(
            consultation=document.consultation,
            analysis_type='document',
            content=json.dumps(analysis),
            metadata={'file_type': document.file.name.split('.')[-1]}
        )
        
        messages.success(request, "Document analysis completed successfully.")
    except Exception as e:
        logger.error(f"Error analyzing document: {str(e)}")
        messages.error(request, "Error analyzing document. Please try again.")
    
    return redirect('core:consultation_detail', consultation_id=document.consultation.id)

@login_required
def consultation_insights(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id)
    
    if not request.user.is_staff and consultation.user != request.user:
        messages.error(request, "You don't have permission to view these insights.")
        return redirect('core:consultation_detail', consultation_id=consultation_id)
    
    # Get all AI analyses for this consultation
    analyses = AIAnalysis.objects.filter(consultation=consultation).order_by('-created_at')
    
    return render(request, 'core/consultation_insights.html', {
        'consultation': consultation,
        'analyses': analyses
    })

# Add a function to send reminder emails
def send_consultation_reminders():
    tomorrow = timezone.now() + timezone.timedelta(days=1)
    consultations = Consultation.objects.filter(
        date=tomorrow.date(),
        status='confirmed',
        mode='virtual'
    )
    
    for consultation in consultations:
        if consultation.meeting_link:
            # Send reminder to client
            send_mail(
                'Reminder: Virtual Consultation Tomorrow - Costsecon Accounting',
                f'''
                Dear {consultation.user.get_full_name()},

                This is a reminder for your virtual consultation tomorrow.

                Consultation Details:
                Service: {consultation.service.name}
                Date: {consultation.date.strftime('%B %d, %Y')}
                Time: {consultation.time.strftime('%I:%M %p')}

                Meeting Link: {consultation.meeting_link}

                Please join the meeting 5 minutes before the scheduled time.

                Best regards,
                Costsecon Accounting Team
                ''',
                settings.DEFAULT_FROM_EMAIL,
                [consultation.user.email],
                fail_silently=False,
            )
            
            # Send reminder to admin
            send_mail(
                'Reminder: Virtual Consultation Tomorrow - Costsecon Accounting',
                f'''
                Reminder: Virtual consultation scheduled for tomorrow:

                Client: {consultation.user.get_full_name()}
                Service: {consultation.service.name}
                Date: {consultation.date.strftime('%B %d, %Y')}
                Time: {consultation.time.strftime('%I:%M %p')}
                Meeting Link: {consultation.meeting_link}

                Please prepare for the consultation.
                ''',
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=False,
            )

@login_required
def update_consultation(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id, user=request.user)
    
    if request.method == 'POST':
        form = ConsultationForm(request.POST, instance=consultation)
        if form.is_valid():
            updated_consultation = form.save(commit=False)
            
            # Check if mode changed to virtual
            if updated_consultation.mode == 'virtual' and not updated_consultation.meeting_link:
                # Generate a random meeting ID
                meeting_id = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
                meeting_link = f"https://meet.google.com/{meeting_id}"
                updated_consultation.meeting_link = meeting_link
                
                # Send email to client
                send_mail(
                    'Virtual Consultation Link - Costsecon Accounting',
                    f'''
                    Dear {updated_consultation.user.get_full_name()},

                    Your virtual consultation has been updated!

                    Consultation Details:
                    Service: {updated_consultation.service.name}
                    Date: {updated_consultation.date.strftime('%B %d, %Y')}
                    Time: {updated_consultation.time.strftime('%I:%M %p')}

                    Meeting Link: {meeting_link}

                    Please join the meeting 5 minutes before the scheduled time.

                    Best regards,
                    Costsecon Accounting Team
                    ''',
                    settings.DEFAULT_FROM_EMAIL,
                    [updated_consultation.user.email],
                    fail_silently=False,
                )
                
                # Send email to admin
                send_mail(
                    'Updated Virtual Consultation - Costsecon Accounting',
                    f'''
                    Virtual consultation has been updated:

                    Client: {updated_consultation.user.get_full_name()}
                    Service: {updated_consultation.service.name}
                    Date: {updated_consultation.date.strftime('%B %d, %Y')}
                    Time: {updated_consultation.time.strftime('%I:%M %p')}
                    Meeting Link: {meeting_link}

                    Please prepare for the consultation.
                    ''',
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                    fail_silently=False,
                )
            
            updated_consultation.save()
            messages.success(request, 'Consultation updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ConsultationForm(instance=consultation)
    
    return render(request, 'core/update_consultation.html', {
        'form': form,
        'consultation': consultation
    })

@login_required
def delete_consultation(request, consultation_id):
    consultation = get_object_or_404(Consultation, id=consultation_id, user=request.user)
    
    if request.method == 'POST':
        try:
            consultation.delete()
            messages.success(request, 'Consultation deleted successfully!')
            return redirect('accounts:profile')
        except Exception as e:
            messages.error(request, f'Error deleting consultation: {str(e)}')
            return redirect('accounts:profile')
    
    return render(request, 'core/delete_consultation.html', {
        'consultation': consultation
    })

@login_required
def delete_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    
    # Only staff can delete documents
    if not request.user.is_staff:
        raise PermissionDenied
    
    service_id = document.service.id
    document.delete()
    messages.success(request, 'Document deleted successfully.')
    return redirect('service_detail', pk=service_id)
