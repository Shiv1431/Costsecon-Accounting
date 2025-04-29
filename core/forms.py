from django import forms
from .models import Consultation, Feedback, Service, Contact, Document
from django.utils import timezone

class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['date', 'time', 'mode', 'notes', 'supporting_documents', 'additional_documents']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'mode': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'supporting_documents': forms.FileInput(attrs={'class': 'form-control'}),
            'additional_documents': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.service = kwargs.pop('service', None)
        super().__init__(*args, **kwargs)
        
        if self.service:
            # Add service-specific fields
            for field in self.service.required_fields:
                if field == 'tax_year':
                    self.fields['tax_year'] = forms.CharField(
                        max_length=9,
                        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2023-2024'})
                    )
                elif field == 'financial_year':
                    self.fields['financial_year'] = forms.CharField(
                        max_length=9,
                        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 2023-2024'})
                    )
                elif field == 'company_name':
                    self.fields['company_name'] = forms.CharField(
                        max_length=100,
                        widget=forms.TextInput(attrs={'class': 'form-control'})
                    )
                elif field == 'gst_number':
                    self.fields['gst_number'] = forms.CharField(
                        max_length=15,
                        widget=forms.TextInput(attrs={'class': 'form-control'})
                    )
                elif field == 'pan_number':
                    self.fields['pan_number'] = forms.CharField(
                        max_length=10,
                        widget=forms.TextInput(attrs={'class': 'form-control'})
                    )
                elif field == 'number_of_employees':
                    self.fields['number_of_employees'] = forms.IntegerField(
                        widget=forms.NumberInput(attrs={'class': 'form-control'})
                    )
                elif field == 'business_type':
                    self.fields['business_type'] = forms.ChoiceField(
                        choices=[
                            ('sole_proprietorship', 'Sole Proprietorship'),
                            ('partnership', 'Partnership'),
                            ('private_limited', 'Private Limited'),
                            ('public_limited', 'Public Limited'),
                            ('llp', 'Limited Liability Partnership')
                        ],
                        widget=forms.Select(attrs={'class': 'form-control'})
                    )
                elif field == 'consultation_type':
                    self.fields['consultation_type'] = forms.ChoiceField(
                        choices=[
                            ('tax', 'Tax Planning'),
                            ('financial', 'Financial Planning'),
                            ('business', 'Business Strategy'),
                            ('compliance', 'Regulatory Compliance'),
                            ('other', 'Other')
                        ],
                        widget=forms.Select(attrs={'class': 'form-control'})
                    )
                elif field == 'current_challenges':
                    self.fields['current_challenges'] = forms.CharField(
                        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
                    )
                elif field == 'goals':
                    self.fields['goals'] = forms.CharField(
                        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
                    )
                elif field.endswith('_documents') or field.endswith('_statements') or field.endswith('_invoices') or field.endswith('_receipts'):
                    self.fields[field] = forms.FileField(
                        widget=forms.FileInput(attrs={'class': 'form-control'})
                    )
        
        # Set minimum date to today
        self.fields['date'].widget.attrs['min'] = timezone.now().date().isoformat()

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['service_rating', 'consultant_rating', 'service_comment', 'consultant_comment']
        widgets = {
            'service_rating': forms.Select(attrs={'class': 'form-control'}),
            'consultant_rating': forms.Select(attrs={'class': 'form-control'}),
            'service_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'consultant_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        consultation = kwargs.pop('consultation', None)
        super().__init__(*args, **kwargs)
        
        # Hide consultant rating if no consultant is assigned
        if consultation and not consultation.consultant:
            del self.fields['consultant_rating']
            del self.fields['consultant_comment']

class ServiceFilterForm(forms.Form):
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    mode = forms.ChoiceField(choices=[('', 'All')] + list(Consultation.MODE_CHOICES), required=False)
    service = forms.ModelChoiceField(queryset=Service.objects.all(), required=False, empty_label="All Services")

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['name', 'file', 'description', 'is_private']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        } 