from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('services/', views.service_list, name='service_list'),
    path('services/<int:pk>/', views.ServiceDetailView.as_view(), name='service_detail'),
    path('book-consultation/<int:service_id>/', views.book_consultation, name='book_consultation'),
    path('payment/<int:consultation_id>/', views.payment, name='payment'),
    path('verify-payment/<int:consultation_id>/', views.verify_payment, name='verify_payment'),
    path('my-consultations/', views.my_consultations, name='my_consultations'),
    path('update-consultation/<int:consultation_id>/', views.update_consultation, name='update_consultation'),
    path('delete-consultation/<int:consultation_id>/', views.delete_consultation, name='delete_consultation'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('consultation/<int:consultation_id>/', views.consultation_detail, name='consultation_detail'),
    path('consultation/<int:consultation_id>/feedback/', views.submit_feedback, name='submit_feedback'),
    path('documents/<int:document_id>/delete/', views.delete_document, name='delete_document'),
] 